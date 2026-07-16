package main

import (
	"math"
	"testing"
)

func sumFloat32(xs []float32) float64 {
	var s float64
	for _, x := range xs {
		s += float64(x)
	}
	return s
}

func TestSoftmaxSumsToOne(t *testing.T) {
	out := softmax([]float32{2, 1, 0.1, -1, 0.5, 3})
	if got := sumFloat32(out); math.Abs(got-1.0) > 1e-6 {
		t.Fatalf("softmax should sum to 1, got %v", got)
	}
}

func TestSoftmaxUniformLogits(t *testing.T) {
	out := softmax([]float32{0, 0, 0, 0, 0, 0})
	for i, p := range out {
		if math.Abs(float64(p)-1.0/6.0) > 1e-6 {
			t.Errorf("index %d: expected 1/6, got %v", i, p)
		}
	}
}

func TestSoftmaxIsMonotonic(t *testing.T) {
	// A larger logit must map to a larger probability.
	out := softmax([]float32{0, 1, 2})
	if !(out[0] < out[1] && out[1] < out[2]) {
		t.Errorf("expected strictly increasing probabilities, got %v", out)
	}
}

func TestSoftmaxKnownValue(t *testing.T) {
	out := softmax([]float32{1, 0})
	want := math.Exp(1) / (math.Exp(1) + math.Exp(0))
	if math.Abs(float64(out[0])-want) > 1e-6 {
		t.Errorf("expected %v, got %v", want, out[0])
	}
}
