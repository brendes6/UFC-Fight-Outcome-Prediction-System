package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"math"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"

	"cloud.google.com/go/firestore"
	"cloud.google.com/go/storage"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	ort "github.com/yalue/onnxruntime_go"
)

const numModels = 2
const gcsBucket = "ufc-proj-models"

// Model file names: one neural network, one XGBoost (heterogeneous ensemble)
var modelFiles = [numModels]string{"nn_model.onnx", "xgb_model.onnx"}

var finalFeatures = []string{
	"RedWinPct", "BlueWinPct", "WinPctDif", "RedKoPct", "BlueKoPct", "KoPctDif",
	"RedSubPct", "BlueSubPct", "SubPctDif", "RedDecPct", "BlueDecPct", "DecPctDif", "RedLossesByKO", "BlueLossesByKO", "LossesByKODif",
	"RedLossesBySub", "BlueLossesBySub", "LossesBySubDif", "RedLossesByDec", "BlueLossesByDec", "LossesByDecDif", "RedWeightLbs",
	"HeightDif", "ReachDif", "AgeDif", "RedAge", "BlueAge", "SigStrDif", "StrPctDif", "TDDif", "SubAttDif",
	"RedAvgSigStrLanded", "BlueAvgSigStrLanded", "RedAvgTDLanded", "BlueAvgTDLanded", "RedAvgSigStrPct", "BlueAvgSigStrPct",
	"RedAvgSubAtt", "BlueAvgSubAtt", "SigStrAbsorbedDif", "RedSigStrAbsorbed", "BlueSigStrAbsorbed", "AvgRoundsDif",
	"RedAvgRounds", "BlueAvgRounds", "EloDif", "OpponentEloDif", "RedElo", "BlueElo", "WinStreakDif",
	"RedCurrentWinStreak", "BlueCurrentWinStreak", "RedFinishL5", "BlueFinishL5", "FinishL5Dif", "FinishPctDif",
}

// Fighter struct - stores all basic fighter stats
// used for eventual input tensor formatting
type Fighter struct {
	// firestore tag for variable mapping from firestore NoSQL db
	Wins              int     `firestore:"Wins"`
	WinsByKO          int     `firestore:"WinsByKO"`
	WinsBySubmission  int     `firestore:"WinsBySubmission"`
	WinsByDecision    int     `firestore:"WinsByDecision"`
	Losses            int     `firestore:"Losses"`
	HeightCms         float64 `firestore:"HeightCms"`
	ReachCms          float64 `firestore:"ReachCms"`
	AvgSigStrLanded   float64 `firestore:"AvgSigStrLanded"`
	AvgTDLanded       float64 `firestore:"AvgTDLanded"`
	AvgSigStrPct      float64 `firestore:"AvgSigStrPct"`
	AvgSubAtt         float64 `firestore:"AvgSubAtt"`
	Stance            string  `firestore:"Stance"`
	WeightLbs         int     `firestore:"WeightLbs"`
	Age               int     `firestore:"Age"`
	KoPct             float64 `firestore:"KoPct"`
	SubPct            float64 `firestore:"SubPct"`
	DecPct            float64 `firestore:"DecPct"`
	AvgRounds         float64 `firestore:"AvgRounds"`
	Elo               float64 `firestore:"Elo"`
	OpponentElo       float64 `firestore:"OpponentElo"`
	SigStrAbsorbed    float64 `firestore:"SigStrAbsorbed"`
	CurrentWinStreak  int     `firestore:"CurrentWinStreak"`
	FinishL5          float64 `firestore:"FinishL5"`
	LossesByKO        int     `firestore:"LossesByKO"`
	LossesBySub       int     `firestore:"LossesBySub"`
	LossesByDec       int     `firestore:"LossesByDec"`
	WinPct            float64 `firestore:"WinPct"`
	TotalRoundsFought int     `firestore:"TotalRoundsFought"`
	WeightClass       string  `firestore:"WeightClass"`
	Gender            string  `firestore:"Gender"`
}

// Struct storing metadata of means/std's for
// our input pre-processing, loaded from GCS blob storage
type ScalerMetadata struct {
	Means      map[string]float64 `json:"means"`
	Stds       map[string]float64 `json:"stds"`
	SavedOrder []string           `json:"saved_order"`
}

type rawScalerMetadata struct {
	Means      json.RawMessage `json:"means"`
	Stds       json.RawMessage `json:"stds"`
	SavedOrder []string        `json:"saved_order"`
}

// Struct for inference results structuring
type PredictionResult struct {
	RedKO   float32 `json:"red_ko"`
	RedSub  float32 `json:"red_sub"`
	RedDec  float32 `json:"red_dec"`
	BlueKO  float32 `json:"blue_ko"`
	BlueSub float32 `json:"blue_sub"`
	BlueDec float32 `json:"blue_dec"`
}

// Softmax function - needed to convert NN logits output
// into real probabilities
func softmax(logits []float32) []float32 {
	var sum float64
	probabilities := make([]float32, len(logits))
	for _, v := range logits {
		sum += math.Exp(float64(v))
	}
	for i, v := range logits {
		probabilities[i] = float32(math.Exp(float64(v)) / sum)
	}
	return probabilities
}

func valuesByFeature(raw json.RawMessage, names []string, fieldName string) (map[string]float64, error) {
	values := map[string]float64{}
	if err := json.Unmarshal(raw, &values); err == nil {
		return values, nil
	}

	var orderedValues []float64
	if err := json.Unmarshal(raw, &orderedValues); err != nil {
		return nil, fmt.Errorf("invalid scaler %s: %v", fieldName, err)
	}
	if len(orderedValues) != len(names) {
		return nil, fmt.Errorf("invalid scaler %s length: got %d, want %d", fieldName, len(orderedValues), len(names))
	}
	for i, name := range names {
		values[name] = orderedValues[i]
	}
	return values, nil
}

func parseScalerMetadata(data []byte) (*ScalerMetadata, error) {
	var raw rawScalerMetadata
	if err := json.Unmarshal(data, &raw); err != nil {
		return nil, err
	}

	savedOrder := raw.SavedOrder
	if len(savedOrder) == 0 {
		savedOrder = finalFeatures
	}

	means, err := valuesByFeature(raw.Means, savedOrder, "means")
	if err != nil {
		return nil, err
	}
	stds, err := valuesByFeature(raw.Stds, savedOrder, "stds")
	if err != nil {
		return nil, err
	}

	meta := &ScalerMetadata{
		Means:      means,
		Stds:       stds,
		SavedOrder: savedOrder,
	}
	if err := validateScalerMetadata(meta); err != nil {
		return nil, err
	}
	return meta, nil
}

func validateScalerMetadata(meta *ScalerMetadata) error {
	if len(meta.SavedOrder) != len(finalFeatures) {
		return fmt.Errorf("invalid scaler feature count: got %d, want %d", len(meta.SavedOrder), len(finalFeatures))
	}
	for i, name := range finalFeatures {
		if meta.SavedOrder[i] != name {
			return fmt.Errorf("invalid scaler feature order at %d: got %s, want %s", i, meta.SavedOrder[i], name)
		}
		mean, ok := meta.Means[name]
		if !ok || math.IsNaN(mean) || math.IsInf(mean, 0) {
			return fmt.Errorf("invalid scaler mean for %s", name)
		}
		std, ok := meta.Stds[name]
		if !ok || std == 0 || math.IsNaN(std) || math.IsInf(std, 0) {
			return fmt.Errorf("invalid scaler std for %s", name)
		}
	}
	return nil
}

// Downloads scaler params JSON from GCS and parses into ScalerMetadata
func loadScalerFromGCS(ctx context.Context) *ScalerMetadata {
	client, err := storage.NewClient(ctx)
	if err != nil {
		panic(fmt.Sprintf("Failed to create GCS client: %v", err))
	}
	defer client.Close()

	reader, err := client.Bucket(gcsBucket).Object("production/scaler_params.json").NewReader(ctx)
	if err != nil {
		panic(fmt.Sprintf("Failed to read scaler from GCS: %v", err))
	}
	defer reader.Close()

	data, err := io.ReadAll(reader)
	if err != nil {
		panic(fmt.Sprintf("Failed to read scaler data: %v", err))
	}

	meta, err := parseScalerMetadata(data)
	if err != nil {
		panic(fmt.Sprintf("Failed to parse scaler JSON: %v", err))
	}

	slog.Info("loaded scaler from GCS", "features", len(meta.SavedOrder))
	return meta
}

// Downloads ONNX model files from GCS to local disk
func downloadModelsFromGCS(ctx context.Context) {
	client, err := storage.NewClient(ctx)
	if err != nil {
		panic(fmt.Sprintf("Failed to create GCS client: %v", err))
	}
	defer client.Close()

	var wg sync.WaitGroup
	for i := 0; i < numModels; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			fileName := modelFiles[idx]
			gcsPath := fmt.Sprintf("production/%s", fileName)

			reader, err := client.Bucket(gcsBucket).Object(gcsPath).NewReader(ctx)
			if err != nil {
				panic(fmt.Sprintf("Failed to download %s from GCS: %v", gcsPath, err))
			}
			defer reader.Close()

			file, err := os.Create(fileName)
			if err != nil {
				panic(fmt.Sprintf("Failed to create local file %s: %v", fileName, err))
			}
			defer file.Close()

			if _, err := io.Copy(file, reader); err != nil {
				panic(fmt.Sprintf("Failed to write %s: %v", fileName, err))
			}
			slog.Info("downloaded model from GCS", "file", fileName)
		}(i)
	}
	wg.Wait()
}

// Initializes our firestore client for database reads
func initFirestore(ctx context.Context) *firestore.Client {
	projectID := "ufc-proj"
	databaseID := "ufcdb"

	client, err := firestore.NewClientWithDatabase(ctx, projectID, databaseID)
	if err != nil {
		panic(fmt.Sprintf("Failed to create Firestore client: %v", err))
	}
	return client
}

// ModelSession struct storing information for our ONNX session
type ModelSession struct {
	// mutex serializes access to the reusable input/output tensors below so that
	// concurrent /predict requests can safely share a single session.
	mu           sync.Mutex
	Session      *ort.AdvancedSession
	InputTensor  *ort.Tensor[float32]
	OutputTensor *ort.Tensor[float32]
	// XGBoost ONNX models output labels + probabilities separately
	LabelTensor *ort.Tensor[int64]
	IsTreeModel bool // true for XGBoost, false for NN
}

// Initialize a neural network ONNX model session
// NN outputs raw logits as a single [1,6] tensor
func initNNModel(modelPath string) (*ModelSession, error) {
	inputTensor, err := ort.NewEmptyTensor[float32](ort.NewShape(1, 56))
	if err != nil {
		return nil, fmt.Errorf("create input tensor: %w", err)
	}
	outputTensor, err := ort.NewEmptyTensor[float32](ort.NewShape(1, 6))
	if err != nil {
		return nil, fmt.Errorf("create output tensor: %w", err)
	}

	session, err := ort.NewAdvancedSession(modelPath,
		[]string{"input"}, []string{"output"},
		[]ort.Value{inputTensor}, []ort.Value{outputTensor}, nil)
	if err != nil {
		return nil, fmt.Errorf("create NN session: %w", err)
	}

	return &ModelSession{
		Session:      session,
		InputTensor:  inputTensor,
		OutputTensor: outputTensor,
		IsTreeModel:  false,
	}, nil
}

// Initialize an XGBoost ONNX model session
// XGBoost ONNX models output (labels int64, probabilities float32)
func initXGBModel(modelPath string) (*ModelSession, error) {
	inputTensor, err := ort.NewEmptyTensor[float32](ort.NewShape(1, 56))
	if err != nil {
		return nil, fmt.Errorf("create input tensor: %w", err)
	}
	labelTensor, err := ort.NewEmptyTensor[int64](ort.NewShape(1))
	if err != nil {
		return nil, fmt.Errorf("create label tensor: %w", err)
	}
	outputTensor, err := ort.NewEmptyTensor[float32](ort.NewShape(1, 6))
	if err != nil {
		return nil, fmt.Errorf("create output tensor: %w", err)
	}

	session, err := ort.NewAdvancedSession(modelPath,
		[]string{"input"}, []string{"label", "probabilities"},
		[]ort.Value{inputTensor}, []ort.Value{labelTensor, outputTensor}, nil)
	if err != nil {
		return nil, fmt.Errorf("create XGB session: %w", err)
	}

	return &ModelSession{
		Session:      session,
		InputTensor:  inputTensor,
		OutputTensor: outputTensor,
		LabelTensor:  labelTensor,
		IsTreeModel:  true,
	}, nil
}

// Initialize all ONNX models concurrently
// Downloads models from GCS first, then loads them into ONNX sessions
func initAllModels(ctx context.Context) []*ModelSession {
	// Download latest models from GCS blob storage
	downloadModelsFromGCS(ctx)

	ort.SetSharedLibraryPath("onnxruntime.so")
	if err := ort.InitializeEnvironment(); err != nil {
		panic(fmt.Sprintf("Failed to initialize ONNX runtime: %v", err))
	}

	sessions := make([]*ModelSession, numModels)
	errs := make([]error, numModels)
	var wg sync.WaitGroup

	for i := 0; i < numModels; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			var (
				ms  *ModelSession
				err error
			)
			// Model 0 is the neural network; the rest are XGBoost.
			if idx == 0 {
				ms, err = initNNModel(modelFiles[idx])
			} else {
				ms, err = initXGBModel(modelFiles[idx])
			}
			if err != nil {
				errs[idx] = err
				return
			}
			sessions[idx] = ms
		}(i)
	}
	wg.Wait()

	for idx, err := range errs {
		if err != nil {
			panic(fmt.Sprintf("Failed to initialize model %s: %v", modelFiles[idx], err))
		}
	}
	return sessions
}

// Function to run inference using our ONNX session
// Returns probabilities: for NN models, applies softmax to logits;
// for XGBoost models, output is already probabilities.
//
// Each ModelSession owns one reusable input/output tensor, so concurrent
// requests must not run the same session at once. The mutex serializes access
// per model while still allowing different models to run in parallel.
func runInference(ms *ModelSession, features []float32) ([]float32, error) {
	ms.mu.Lock()
	copy(ms.InputTensor.GetData(), features)

	if err := ms.Session.Run(); err != nil {
		ms.mu.Unlock()
		return nil, fmt.Errorf("model run failed: %w", err)
	}

	// Copy output before releasing the lock (the tensor is reused next call).
	output := make([]float32, len(ms.OutputTensor.GetData()))
	copy(output, ms.OutputTensor.GetData())
	ms.mu.Unlock()

	// NN outputs raw logits → apply softmax
	// XGBoost ONNX outputs probabilities directly
	if !ms.IsTreeModel {
		output = softmax(output)
	}

	return output, nil
}

// Run all models concurrently and average their probabilities.
// Heterogeneous ensemble: NN (smooth boundaries) + XGBoost (step boundaries)
// provides real diversity — different model families make different errors.
func runEnsembleInference(sessions []*ModelSession, features []float32) ([]float32, error) {
	numClasses := 6
	results := make([][]float32, numModels)
	errs := make([]error, numModels)
	var wg sync.WaitGroup

	// Run each model concurrently
	for i := 0; i < numModels; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			probs, err := runInference(sessions[idx], features)
			if err != nil {
				errs[idx] = err
				return
			}
			results[idx] = probs
		}(i)
	}
	wg.Wait()

	for _, err := range errs {
		if err != nil {
			return nil, err
		}
	}

	// Average probabilities across both models
	averaged := make([]float32, numClasses)
	for _, probs := range results {
		for j := 0; j < numClasses; j++ {
			averaged[j] += probs[j]
		}
	}
	for j := 0; j < numClasses; j++ {
		averaged[j] /= float32(numModels)
	}

	return averaged, nil
}

// Function to get individual fighter stats from our firestore database
// Using channels to support concurrent calls of database
func getFighterStats(ctx context.Context, client *firestore.Client, name string, resChan chan<- *Fighter, errChan chan<- error) {
	docID := strings.TrimSpace(name)

	dsnap, err := client.Collection("fighters").Doc(docID).Get(ctx)
	if err != nil {
		errChan <- fmt.Errorf("fighter %s not found", name)
		return
	}

	var fighter Fighter
	if err := dsnap.DataTo(&fighter); err != nil {
		errChan <- fmt.Errorf("error parsing data for %s: %v", name, err)
		return
	}
	resChan <- &fighter
}

// Function to calculate features given our fighter data
func calculateFeatures(red, blue *Fighter, meta *ScalerMetadata) []float32 {
	features := make([]float32, len(meta.SavedOrder))

	rawStats := map[string]float64{
		"RedWinPct":            red.WinPct,
		"BlueWinPct":           blue.WinPct,
		"WinPctDif":            red.WinPct - blue.WinPct,
		"RedKoPct":             red.KoPct,
		"BlueKoPct":            blue.KoPct,
		"KoPctDif":             red.KoPct - blue.KoPct,
		"RedSubPct":            red.SubPct,
		"BlueSubPct":           blue.SubPct,
		"SubPctDif":            red.SubPct - blue.SubPct,
		"RedDecPct":            red.DecPct,
		"BlueDecPct":           blue.DecPct,
		"DecPctDif":            red.DecPct - blue.DecPct,
		"RedLossesByKO":        float64(red.LossesByKO),
		"BlueLossesByKO":       float64(blue.LossesByKO),
		"LossesByKODif":        float64(red.LossesByKO - blue.LossesByKO),
		"RedLossesBySub":       float64(red.LossesBySub),
		"BlueLossesBySub":      float64(blue.LossesBySub),
		"LossesBySubDif":       float64(red.LossesBySub - blue.LossesBySub),
		"RedLossesByDec":       float64(red.LossesByDec),
		"BlueLossesByDec":      float64(blue.LossesByDec),
		"LossesByDecDif":       float64(red.LossesByDec - blue.LossesByDec),
		"RedWeightLbs":         float64(red.WeightLbs),
		"HeightDif":            red.HeightCms - blue.HeightCms,
		"ReachDif":             red.ReachCms - blue.ReachCms,
		"AgeDif":               float64(red.Age - blue.Age),
		"RedAge":               float64(red.Age),
		"BlueAge":              float64(blue.Age),
		"SigStrDif":            red.AvgSigStrLanded - blue.AvgSigStrLanded,
		"StrPctDif":            red.AvgSigStrPct - blue.AvgSigStrPct,
		"TDDif":                red.AvgTDLanded - blue.AvgTDLanded,
		"SubAttDif":            red.AvgSubAtt - blue.AvgSubAtt,
		"RedAvgSigStrLanded":   red.AvgSigStrLanded,
		"BlueAvgSigStrLanded":  blue.AvgSigStrLanded,
		"RedAvgTDLanded":       red.AvgTDLanded,
		"BlueAvgTDLanded":      blue.AvgTDLanded,
		"RedAvgSigStrPct":      red.AvgSigStrPct,
		"BlueAvgSigStrPct":     blue.AvgSigStrPct,
		"RedAvgSubAtt":         red.AvgSubAtt,
		"BlueAvgSubAtt":        blue.AvgSubAtt,
		"SigStrAbsorbedDif":    red.SigStrAbsorbed - blue.SigStrAbsorbed,
		"RedSigStrAbsorbed":    red.SigStrAbsorbed,
		"BlueSigStrAbsorbed":   blue.SigStrAbsorbed,
		"AvgRoundsDif":         red.AvgRounds - blue.AvgRounds,
		"RedAvgRounds":         red.AvgRounds,
		"BlueAvgRounds":        blue.AvgRounds,
		"EloDif":               red.Elo - blue.Elo,
		"OpponentEloDif":       red.OpponentElo - blue.OpponentElo,
		"RedElo":               red.Elo,
		"BlueElo":              blue.Elo,
		"WinStreakDif":         float64(red.CurrentWinStreak - blue.CurrentWinStreak),
		"RedCurrentWinStreak":  float64(red.CurrentWinStreak),
		"BlueCurrentWinStreak": float64(blue.CurrentWinStreak),
		"RedFinishL5":          float64(red.FinishL5),
		"BlueFinishL5":         float64(blue.FinishL5),
		"FinishL5Dif":          float64(red.FinishL5 - blue.FinishL5),
		"FinishPctDif":         (float64(red.WinsByKO+red.WinsBySubmission) / math.Max(float64(red.Wins), 1)) - (float64(blue.WinsByKO+blue.WinsBySubmission) / math.Max(float64(blue.Wins), 1)),
	}

	// From our metadata, calculate scaled values and add to our features slice
	for i, name := range meta.SavedOrder {
		rawValue, ok := rawStats[name]
		if !ok {
			panic(fmt.Sprintf("missing raw feature %s", name))
		}
		mean := meta.Means[name]
		std := meta.Stds[name]

		features[i] = float32((rawValue - mean) / std)
	}

	return features
}

func main() {
	// Structured JSON logging (plays well with Cloud Run log ingestion).
	slog.SetDefault(slog.New(slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{Level: slog.LevelInfo})))

	// Initialize router and context
	router := gin.Default()

	// CORS configuration to allow our frontend
	// to communicate with our backend
	router.Use(cors.New(cors.Config{
		AllowOrigins: []string{
			"http://localhost:5174",
			"https://mma-predictor.vercel.app",
		},
		AllowMethods:     []string{"GET", "POST", "OPTIONS"},
		AllowHeaders:     []string{"Content-Type", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
	}))

	ctx := context.Background()

	// Initialize redis client - redis used to minimize inference
	// time for common matchups
	rdb := redis.NewClient(&redis.Options{
		Addr:     os.Getenv("REDIS_URL"),
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       0,
	})

	if err := rdb.Ping(ctx).Err(); err != nil {
		panic(fmt.Sprintf("Failed to connect to Redis: %v", err))
	}

	// Concurrently initialize firestore, load models from GCS, and load scaler from GCS
	dbChan := make(chan *firestore.Client, 1)
	onnxChan := make(chan []*ModelSession, 1)
	scalerChan := make(chan *ScalerMetadata, 1)

	var db *firestore.Client
	var onnxSessions []*ModelSession
	var scalerMeta *ScalerMetadata

	go func() {
		dbChan <- initFirestore(ctx)
	}()

	go func() {
		onnxChan <- initAllModels(ctx)
	}()

	go func() {
		scalerChan <- loadScalerFromGCS(ctx)
	}()

	db = <-dbChan
	onnxSessions = <-onnxChan
	scalerMeta = <-scalerChan

	router.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"message": "Welcome to the UFC Predictions API"})
	})

	// Lightweight liveness probe for Cloud Run / uptime checks.
	router.GET("/healthz", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "ok"})
	})

	// Endpoint for /predict - returns an ensemble prediction for a matchup
	router.POST("/predict", func(c *gin.Context) {
		// Struct binding red and blue fighters from context
		var req struct {
			RedFighter  string `json:"red_fighter" binding:"required"`
			BlueFighter string `json:"blue_fighter" binding:"required"`
		}
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		ctx := c.Request.Context()

		// Check if prediction is cached in Redis
		cacheKey := fmt.Sprintf("%s:%s", req.RedFighter, req.BlueFighter)
		if cached, err := rdb.Get(ctx, cacheKey).Result(); err == nil {
			var result PredictionResult
			if json.Unmarshal([]byte(cached), &result) == nil {
				slog.Debug("prediction cache hit", "key", cacheKey)
				c.JSON(http.StatusOK, result)
				return
			}
		}

		// Concurrently fetch both fighter stats from Firestore
		redChan := make(chan *Fighter, 1)
		blueChan := make(chan *Fighter, 1)
		errChan := make(chan error, 2)

		go getFighterStats(ctx, db, req.RedFighter, redChan, errChan)
		go getFighterStats(ctx, db, req.BlueFighter, blueChan, errChan)

		// Collect results
		var red, blue *Fighter
		for received := 0; received < 2; {
			select {
			case f := <-redChan:
				red = f
				received++
			case b := <-blueChan:
				blue = b
				received++
			case err := <-errChan:
				c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
				return
			}
		}

		// Engineer and scale features using pre-loaded scaler from GCS
		features := calculateFeatures(red, blue, scalerMeta)

		// Run ensemble inference: all models concurrently, then average
		ensembleProbs, err := runEnsembleInference(onnxSessions, features)
		if err != nil {
			slog.Error("inference failed", "key", cacheKey, "error", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "prediction failed"})
			return
		}

		result := PredictionResult{
			RedKO: ensembleProbs[0], RedSub: ensembleProbs[1],
			RedDec: ensembleProbs[2],
			BlueKO: ensembleProbs[3], BlueSub: ensembleProbs[4],
			BlueDec: ensembleProbs[5],
		}

		// Store prediction result in Redis cache
		if jsonBytes, err := json.Marshal(result); err == nil {
			rdb.Set(ctx, cacheKey, jsonBytes, 6*time.Hour)
		}

		c.JSON(http.StatusOK, result)
	})

	// Endpoint for /upcoming - returns all upcoming fight predictions
	router.GET("/upcoming", func(c *gin.Context) {
		ctx := c.Request.Context()

		// Query all documents from the "upcoming" collection
		docs, err := db.Collection("upcoming").Documents(ctx).GetAll()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to fetch upcoming fights: %v", err)})
			return
		}

		// Convert documents to slice of UpcomingFight
		var upcomingFights []map[string]interface{}
		for _, doc := range docs {
			data := doc.Data()
			upcomingFights = append(upcomingFights, data)
		}

		c.JSON(http.StatusOK, gin.H{"fights": upcomingFights})
	})

	// Endpoint for /previous - returns all previous fight predictions with results
	router.GET("/previous", func(c *gin.Context) {
		ctx := c.Request.Context()

		// Query all documents from the "previous" collection
		docs, err := db.Collection("previous").Documents(ctx).GetAll()
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": fmt.Sprintf("Failed to fetch previous fights: %v", err)})
			return
		}

		// Convert documents to slice
		var previousFights []map[string]interface{}
		for _, doc := range docs {
			data := doc.Data()
			previousFights = append(previousFights, data)
		}

		c.JSON(http.StatusOK, gin.H{"fights": previousFights})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080" // Default for local
	}

	srv := &http.Server{
		Addr:    ":" + port,
		Handler: router,
	}

	// Serve in a goroutine so the main goroutine can wait for a shutdown signal.
	go func() {
		slog.Info("server listening", "port", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			panic(fmt.Sprintf("server error: %v", err))
		}
	}()

	// Block until an interrupt/termination signal arrives (Cloud Run sends SIGTERM).
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, os.Interrupt, syscall.SIGTERM)
	<-quit
	slog.Info("shutting down server")

	// Give in-flight requests up to 10s to finish, then release resources.
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	if err := srv.Shutdown(shutdownCtx); err != nil {
		slog.Error("forced shutdown", "error", err)
	}
	if err := db.Close(); err != nil {
		slog.Error("closing firestore client", "error", err)
	}
	if err := rdb.Close(); err != nil {
		slog.Error("closing redis client", "error", err)
	}
	slog.Info("server stopped")
}
