package main

import (
	"context"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
)

// testPool connects to a real Postgres for integration tests. These tests are
// skipped unless TEST_DATABASE_URL points at a migrated database (so CI, which
// has no Postgres, stays green). Run locally with:
//
//	make db-reset
//	TEST_DATABASE_URL=postgres://ufc:ufc@localhost:5432/ufc go test ./...
func testPool(t *testing.T) *pgxpool.Pool {
	t.Helper()
	dsn := os.Getenv("TEST_DATABASE_URL")
	if dsn == "" {
		t.Skip("TEST_DATABASE_URL not set; skipping Postgres integration test")
	}
	pool, err := pgxpool.New(context.Background(), dsn)
	if err != nil {
		t.Fatalf("connect: %v", err)
	}
	if err := pool.Ping(context.Background()); err != nil {
		t.Fatalf("ping: %v", err)
	}
	return pool
}

func TestGetFighterStatsIntegration(t *testing.T) {
	pool := testPool(t)
	defer pool.Close()
	ctx := context.Background()

	// Populate only a subset of columns; the rest stay NULL and must scan as
	// zero values via the COALESCE-wrapped SELECT.
	_, err := pool.Exec(ctx,
		`INSERT INTO fighters ("fighter_tag","Wins","WinPct","Stance")
		 VALUES ($1,$2,$3,$4)
		 ON CONFLICT ("fighter_tag") DO UPDATE
		   SET "Wins"=EXCLUDED."Wins","WinPct"=EXCLUDED."WinPct","Stance"=EXCLUDED."Stance"`,
		"test_fighter_xyz", 21, 0.84, "Orthodox")
	if err != nil {
		t.Fatalf("insert: %v", err)
	}
	defer pool.Exec(ctx, `DELETE FROM fighters WHERE "fighter_tag"=$1`, "test_fighter_xyz")

	resChan := make(chan *Fighter, 1)
	errChan := make(chan error, 1)
	getFighterStats(ctx, pool, "test_fighter_xyz", resChan, errChan)

	select {
	case f := <-resChan:
		if f.Wins != 21 || f.WinPct != 0.84 || f.Stance != "Orthodox" {
			t.Fatalf("unexpected populated fields: %+v", f)
		}
		if f.Losses != 0 || f.HeightCms != 0 {
			t.Fatalf("expected NULL columns to scan as zero, got Losses=%d HeightCms=%f", f.Losses, f.HeightCms)
		}
	case err := <-errChan:
		t.Fatalf("getFighterStats error: %v", err)
	}
}

func TestGetFighterStatsNotFound(t *testing.T) {
	pool := testPool(t)
	defer pool.Close()

	resChan := make(chan *Fighter, 1)
	errChan := make(chan error, 1)
	getFighterStats(context.Background(), pool, "no_such_fighter_123", resChan, errChan)

	select {
	case <-resChan:
		t.Fatal("expected not-found error, got a fighter")
	case err := <-errChan:
		if err == nil {
			t.Fatal("expected a not-found error")
		}
	}
}

func TestQueryFightCardsIntegration(t *testing.T) {
	pool := testPool(t)
	defer pool.Close()
	ctx := context.Background()

	_, err := pool.Exec(ctx,
		`INSERT INTO upcoming (doc_id, data) VALUES ($1,$2)
		 ON CONFLICT (doc_id) DO UPDATE SET data=EXCLUDED.data`,
		"test_card_1", []byte(`{"red_tag":"a","blue_tag":"b","red_win":0.6}`))
	if err != nil {
		t.Fatalf("insert: %v", err)
	}
	defer pool.Exec(ctx, `DELETE FROM upcoming WHERE doc_id=$1`, "test_card_1")

	cards, err := queryFightCards(ctx, pool, "upcoming")
	if err != nil {
		t.Fatalf("queryFightCards: %v", err)
	}
	found := false
	for _, c := range cards {
		if c["red_tag"] == "a" && c["blue_tag"] == "b" {
			found = true
		}
	}
	if !found {
		t.Fatalf("inserted card not returned: %+v", cards)
	}
}
