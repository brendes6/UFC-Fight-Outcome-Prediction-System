package main

import (
	"encoding/json"
	"testing"
)

// buildScalerJSON returns a valid scaler payload (dict form) whose values can be
// tweaked via mutate to exercise the validation paths.
func buildScalerJSON(t *testing.T, mutate func(means, stds map[string]float64)) []byte {
	t.Helper()
	means := map[string]float64{}
	stds := map[string]float64{}
	for _, f := range finalFeatures {
		means[f] = 1.0
		stds[f] = 2.0
	}
	if mutate != nil {
		mutate(means, stds)
	}
	b, err := json.Marshal(map[string]any{
		"feature_version": featureVersion,
		"means":           means,
		"stds":            stds,
		"saved_order":     finalFeatures,
	})
	if err != nil {
		t.Fatalf("marshal scaler json: %v", err)
	}
	return b
}

func TestParseScalerDictForm(t *testing.T) {
	meta, err := parseScalerMetadata(buildScalerJSON(t, nil))
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(meta.SavedOrder) != len(finalFeatures) {
		t.Fatalf("expected %d features, got %d", len(finalFeatures), len(meta.SavedOrder))
	}
	if meta.Means["RedElo"] != 1.0 || meta.Stds["RedElo"] != 2.0 {
		t.Errorf("unexpected mean/std for RedElo: %v / %v", meta.Means["RedElo"], meta.Stds["RedElo"])
	}
}

func TestParseScalerOrderedArrayForm(t *testing.T) {
	means := make([]float64, len(finalFeatures))
	stds := make([]float64, len(finalFeatures))
	for i := range finalFeatures {
		means[i] = 0.5
		stds[i] = 1.5
	}
	b, _ := json.Marshal(map[string]any{"feature_version": featureVersion, "means": means, "stds": stds, "saved_order": finalFeatures})

	meta, err := parseScalerMetadata(b)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if meta.Means[finalFeatures[0]] != 0.5 || meta.Stds[finalFeatures[0]] != 1.5 {
		t.Errorf("ordered-array values were not mapped by feature name")
	}
}

func TestParseScalerDefaultsSavedOrder(t *testing.T) {
	means := map[string]float64{}
	stds := map[string]float64{}
	for _, f := range finalFeatures {
		means[f] = 1
		stds[f] = 1
	}
	b, _ := json.Marshal(map[string]any{"feature_version": featureVersion, "means": means, "stds": stds}) // no saved_order

	meta, err := parseScalerMetadata(b)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if len(meta.SavedOrder) != len(finalFeatures) {
		t.Errorf("saved_order should default to finalFeatures, got %d", len(meta.SavedOrder))
	}
}

func TestParseScalerRejectsZeroStd(t *testing.T) {
	b := buildScalerJSON(t, func(means, stds map[string]float64) { stds["RedElo"] = 0 })
	if _, err := parseScalerMetadata(b); err == nil {
		t.Fatal("expected error for a zero standard deviation")
	}
}

func TestParseScalerRejectsMissingFeatureVersion(t *testing.T) {
	b := buildScalerJSON(t, nil)
	var payload map[string]any
	if err := json.Unmarshal(b, &payload); err != nil {
		t.Fatal(err)
	}
	delete(payload, "feature_version")
	b, _ = json.Marshal(payload)
	if _, err := parseScalerMetadata(b); err == nil {
		t.Fatal("expected error for missing feature version")
	}
}

func TestParseScalerRejectsWrongLengthArray(t *testing.T) {
	means := make([]float64, len(finalFeatures)-1) // too short
	stds := make([]float64, len(finalFeatures)-1)
	b, _ := json.Marshal(map[string]any{"feature_version": featureVersion, "means": means, "stds": stds, "saved_order": finalFeatures})
	if _, err := parseScalerMetadata(b); err == nil {
		t.Fatal("expected error for wrong-length means array")
	}
}

func TestParseScalerRejectsWrongFeatureOrder(t *testing.T) {
	shuffled := make([]string, len(finalFeatures))
	copy(shuffled, finalFeatures)
	shuffled[0], shuffled[1] = shuffled[1], shuffled[0]

	means := map[string]float64{}
	stds := map[string]float64{}
	for _, f := range finalFeatures {
		means[f] = 1
		stds[f] = 1
	}
	b, _ := json.Marshal(map[string]any{"feature_version": featureVersion, "means": means, "stds": stds, "saved_order": shuffled})
	if _, err := parseScalerMetadata(b); err == nil {
		t.Fatal("expected error when saved_order does not match the canonical feature order")
	}
}
