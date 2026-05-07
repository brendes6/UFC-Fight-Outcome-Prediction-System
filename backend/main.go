package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"strings"
	"sync"
	"time"

	"cloud.google.com/go/firestore"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/redis/go-redis/v9"
	ort "github.com/yalue/onnxruntime_go"
)

const numModels = 4

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
// our input pre-processing, taken from firestore database
type ScalerMetadata struct {
	Means      map[string]float64 `firestore:"means"`
	Stds       map[string]float64 `firestore:"stds"`
	SavedOrder []string           `firestore:"saved_order"`
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

// Gets our metadata from firestore database
func getMetadata(ctx context.Context, client *firestore.Client, metaChan chan<- *ScalerMetadata, errChan chan<- error) {
	// Use channels to support concurrent data fetching.
	// Error channel to handle fetching errors

	dsnap, err := client.Collection("metadata").Doc("scaler_constants").Get(ctx)
	if err != nil {
		errChan <- fmt.Errorf("metadata fetch error: %v", err)
		return
	}
	var meta ScalerMetadata
	if err := dsnap.DataTo(&meta); err != nil {
		errChan <- fmt.Errorf("metadata parse error: %v", err)
		return
	}
	metaChan <- &meta
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
	Session      *ort.AdvancedSession
	InputTensor  *ort.Tensor[float32]
	OutputTensor *ort.Tensor[float32]
}

// Function to initialize our ONNX model and session for inference
func initONNX(modelPath string) ModelSession {
	inputShape := ort.NewShape(1, 56) // 56 input features
	outputShape := ort.NewShape(1, 6) // 6 output classes

	inputTensor, _ := ort.NewEmptyTensor[float32](inputShape)
	outputTensor, _ := ort.NewEmptyTensor[float32](outputShape)

	session, _ := ort.NewAdvancedSession(modelPath,
		[]string{"input"}, []string{"output"},
		[]ort.Value{inputTensor}, []ort.Value{outputTensor}, nil)

	return ModelSession{
		Session:      session,
		InputTensor:  inputTensor,
		OutputTensor: outputTensor,
	}
}

// Initialize all ONNX models concurrently
func initAllModels() []ModelSession {
	ort.SetSharedLibraryPath("onnxruntime.so")
	ort.InitializeEnvironment()

	sessions := make([]ModelSession, numModels)
	var wg sync.WaitGroup

	for i := 0; i < numModels; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			modelPath := fmt.Sprintf("model_%d.onnx", idx)
			sessions[idx] = initONNX(modelPath)
		}(i)
	}
	wg.Wait()
	return sessions
}

// Function to run inference using our ONNX session
func runInference(ms ModelSession, features []float32) []float32 {
	// Get data of our input tensor
	inputData := ms.InputTensor.GetData()
	copy(inputData, features)

	// Run forward pass on our model
	ms.Session.Run()

	// Copy output data (important: copy before another goroutine modifies the tensor)
	output := make([]float32, len(ms.OutputTensor.GetData()))
	copy(output, ms.OutputTensor.GetData())
	return output
}

// Run all models concurrently and average their softmax predictions
func runEnsembleInference(sessions []ModelSession, features []float32) []float32 {
	numClasses := 6
	results := make([][]float32, numModels)
	var wg sync.WaitGroup

	// Run each model concurrently
	for i := 0; i < numModels; i++ {
		wg.Add(1)
		go func(idx int) {
			defer wg.Done()
			logits := runInference(sessions[idx], features)
			results[idx] = softmax(logits)
		}(i)
	}
	wg.Wait()

	// Average the softmax probabilities across all models
	averaged := make([]float32, numClasses)
	for _, probs := range results {
		for j := 0; j < numClasses; j++ {
			averaged[j] += probs[j]
		}
	}
	for j := 0; j < numClasses; j++ {
		averaged[j] /= float32(numModels)
	}

	return averaged
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
		"FinishPctDif":         red.WinPct - blue.WinPct,
	}

	// From our metadata, calculate scaled values and add to our features slice
	for i, name := range meta.SavedOrder {
		rawValue := rawStats[name]
		mean := meta.Means[name]
		std := meta.Stds[name]

		features[i] = float32((rawValue - mean) / std)
	}

	return features
}

func main() {
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

	rdb := redis.NewClient(&redis.Options{
		Addr:     os.Getenv("REDIS_URL"),
		Password: os.Getenv("REDIS_PASSWORD"),
		DB:       0,
	})

	if err := rdb.Ping(ctx).Err(); err != nil {
		panic(fmt.Sprintf("Failed to connect to Redis: %v", err))
	}


	// For concurrent fetching of our firestore client and onnx
	// sessions, we use channels
	dbChan := make(chan *firestore.Client, 1)
	onnxChan := make(chan []ModelSession, 1)

	var db *firestore.Client
	var onnxSessions []ModelSession

	go func() {
		dbChan <- initFirestore(ctx)
	}()

	go func() {
		onnxChan <- initAllModels()
	}()

	db = <-dbChan
	onnxSessions = <-onnxChan

	router.GET("/", func(c *gin.Context) {
		c.JSON(200, gin.H{"message": "Welcome to the UFC Predictions API"})
	})

	// Endpoint for /predict - returns prediction for a given fight
	// Endpoint for /predict
	router.POST("/predict", func(c *gin.Context) {
		// Struct binding red and blue fighters from context
		var req struct {
			RedFighter  string `json:"red_fighter" binding:"required"`
			BlueFighter string `json:"blue_fighter" binding:"required"`
		}
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(400, gin.H{"error": err.Error()})
			return
		}

		ctx := c.Request.Context()

		// Check if prediction is cached in Redis
		cacheKey := fmt.Sprintf("%s:%s", req.RedFighter, req.BlueFighter)
		cached, err := rdb.Get(ctx, cacheKey).Result()
		if err == nil {
			var result PredictionResult
			if json.Unmarshal([]byte(cached), &result) == nil {
				c.JSON(200, result)
				return
			}
		}

		// Concurrently fetch both fighter stats and metadata
		redChan := make(chan *Fighter, 1)
		blueChan := make(chan *Fighter, 1)
		metaChan := make(chan *ScalerMetadata, 1)
		errChan := make(chan error, 3)

		go getFighterStats(ctx, db, req.RedFighter, redChan, errChan)
		go getFighterStats(ctx, db, req.BlueFighter, blueChan, errChan)
		go getMetadata(ctx, db, metaChan, errChan)

		// Collect results
		var red, blue *Fighter
		var meta *ScalerMetadata

		for received := 0; received < 3; {
			select {
			case f := <-redChan:
				red = f
				received++
			case b := <-blueChan:
				blue = b
				received++
			case m := <-metaChan:
				meta = m
				received++
			case err := <-errChan:
				c.JSON(404, gin.H{"error": err.Error()})
				return
			}
		}

		// Engineer and scale features from fighter stats
		features := calculateFeatures(red, blue, meta)

		// Run ensemble inference: all models concurrently, then average softmax
		ensembleProbs := runEnsembleInference(onnxSessions, features)

		result := PredictionResult{
			RedKO:   ensembleProbs[0], RedSub: ensembleProbs[1],
			RedDec:  ensembleProbs[2],
			BlueKO:  ensembleProbs[3], BlueSub: ensembleProbs[4],
			BlueDec: ensembleProbs[5],
		}

		if jsonBytes, err := json.Marshal(result); err == nil {
			rdb.Set(ctx, cacheKey, jsonBytes, 24*time.Hour)
		}

		c.JSON(200, result)

	})

	// Endpoint for /upcoming - returns all upcoming fight predictions
	router.GET("/upcoming", func(c *gin.Context) {
		ctx := c.Request.Context()

		// Query all documents from the "upcoming" collection
		docs, err := db.Collection("upcoming").Documents(ctx).GetAll()
		if err != nil {
			c.JSON(500, gin.H{"error": fmt.Sprintf("Failed to fetch upcoming fights: %v", err)})
			return
		}

		// Convert documents to slice of UpcomingFight
		var upcomingFights []map[string]interface{}
		for _, doc := range docs {
			data := doc.Data()
			upcomingFights = append(upcomingFights, data)
		}

		c.JSON(200, gin.H{"fights": upcomingFights})
	})

	// Endpoint for /previous - returns all previous fight predictions with results
	router.GET("/previous", func(c *gin.Context) {
		ctx := c.Request.Context()

		// Query all documents from the "previous" collection
		docs, err := db.Collection("previous").Documents(ctx).GetAll()
		if err != nil {
			c.JSON(500, gin.H{"error": fmt.Sprintf("Failed to fetch previous fights: %v", err)})
			return
		}

		// Convert documents to slice
		var previousFights []map[string]interface{}
		for _, doc := range docs {
			data := doc.Data()
			previousFights = append(previousFights, data)
		}

		c.JSON(200, gin.H{"fights": previousFights})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080" // Default for local
	}
	router.Run(":" + port)
}
