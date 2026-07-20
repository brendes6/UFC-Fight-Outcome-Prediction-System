package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"reflect"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

// fighterColumns is the SELECT list backing the Fighter struct, derived once
// from its `db` tags. Identifiers are quoted so Postgres preserves their
// CamelCase (matching the struct field names), and each column is wrapped in
// COALESCE so a NULL scans as the Go zero value (a missing stat reads as 0
// rather than producing a scan error).
var fighterColumns = buildColumnList(reflect.TypeOf(Fighter{}))

func buildColumnList(t reflect.Type) string {
	cols := make([]string, 0, t.NumField())
	for i := 0; i < t.NumField(); i++ {
		f := t.Field(i)
		tag := f.Tag.Get("db")
		if tag == "" || tag == "-" {
			continue
		}
		def := "0"
		if f.Type.Kind() == reflect.String {
			def = "''"
		}
		cols = append(cols, fmt.Sprintf(`COALESCE("%s", %s) AS "%s"`, tag, def, tag))
	}
	return strings.Join(cols, ", ")
}

// initPostgres opens a connection pool from DATABASE_URL, the backend's
// source of fighter and fight-card data.
func initPostgres(ctx context.Context) *pgxpool.Pool {
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		panic("DATABASE_URL is not set")
	}
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		panic(fmt.Sprintf("Failed to create Postgres pool: %v", err))
	}
	if err := pool.Ping(ctx); err != nil {
		panic(fmt.Sprintf("Failed to connect to Postgres: %v", err))
	}
	return pool
}

// getFighterStats fetches a single fighter by tag and sends the result (or an
// error) on the provided channels, so callers can fetch both corners concurrently.
func getFighterStats(ctx context.Context, pool *pgxpool.Pool, name string, resChan chan<- *Fighter, errChan chan<- error) {
	fighterTag := strings.TrimSpace(name)

	query := "SELECT " + fighterColumns + " FROM fighters WHERE fighter_tag = $1"
	rows, err := pool.Query(ctx, query, fighterTag)
	if err != nil {
		errChan <- fmt.Errorf("error querying fighter %s: %v", name, err)
		return
	}

	fighter, err := pgx.CollectExactlyOneRow(rows, pgx.RowToStructByName[Fighter])
	if err != nil {
		errChan <- fmt.Errorf("fighter %s not found", name)
		return
	}
	resChan <- &fighter
}

// queryFightCards returns every row of a JSONB-backed card table (upcoming or
// previous) as a slice of generic maps, preserving the pre-migration API shape.
func queryFightCards(ctx context.Context, pool *pgxpool.Pool, table string) ([]map[string]interface{}, error) {
	rows, err := pool.Query(ctx, "SELECT data FROM "+table)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var fights []map[string]interface{}
	for rows.Next() {
		var raw []byte
		if err := rows.Scan(&raw); err != nil {
			return nil, err
		}
		var doc map[string]interface{}
		if err := json.Unmarshal(raw, &doc); err != nil {
			return nil, err
		}
		fights = append(fights, doc)
	}
	return fights, rows.Err()
}
