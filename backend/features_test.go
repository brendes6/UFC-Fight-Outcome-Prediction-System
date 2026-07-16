package main

import (
	"math"
	"testing"
)

// identityMeta returns scaler metadata that leaves raw feature values unchanged
// (mean 0, std 1), so tests can assert the engineered values directly.
func identityMeta() *ScalerMetadata {
	means := map[string]float64{}
	stds := map[string]float64{}
	for _, f := range finalFeatures {
		means[f] = 0
		stds[f] = 1
	}
	return &ScalerMetadata{Means: means, Stds: stds, SavedOrder: finalFeatures}
}

func featureValue(t *testing.T, feats []float32, name string) float64 {
	t.Helper()
	for i, f := range finalFeatures {
		if f == name {
			return float64(feats[i])
		}
	}
	t.Fatalf("feature %q not found", name)
	return 0
}

func TestCalculateFeatures(t *testing.T) {
	red := &Fighter{WinPct: 0.5, Elo: 1500, Age: 30, Wins: 0, WinsByKO: 0, WinsBySubmission: 0}
	blue := &Fighter{WinPct: 0.25, Elo: 1450, Age: 28, Wins: 10, WinsByKO: 5, WinsBySubmission: 2}

	feats := calculateFeatures(red, blue, identityMeta())

	if len(feats) != len(finalFeatures) {
		t.Fatalf("expected %d features, got %d", len(finalFeatures), len(feats))
	}

	checks := []struct {
		name string
		want float64
	}{
		{"RedWinPct", 0.5},
		{"BlueWinPct", 0.25},
		{"WinPctDif", 0.25},
		{"EloDif", 50},
		{"AgeDif", 2},
		{"RedAge", 30},
		// Red has 0 wins → guarded to /1 → finish pct 0; blue = 7/10 = 0.7.
		{"FinishPctDif", -0.7},
	}
	for _, c := range checks {
		if got := featureValue(t, feats, c.name); math.Abs(got-c.want) > 1e-5 {
			t.Errorf("%s: want %v, got %v", c.name, c.want, got)
		}
	}
}

func TestCalculateFeaturesAppliesScaling(t *testing.T) {
	red := &Fighter{WinPct: 0.8}
	blue := &Fighter{WinPct: 0.2}

	meta := identityMeta()
	// Center RedWinPct on its exact raw value with std 2 → scaled value 0.
	meta.Means["RedWinPct"] = 0.8
	meta.Stds["RedWinPct"] = 2

	feats := calculateFeatures(red, blue, meta)

	if v := featureValue(t, feats, "RedWinPct"); math.Abs(v) > 1e-6 {
		t.Errorf("expected 0 after centering/scaling, got %v", v)
	}
}
