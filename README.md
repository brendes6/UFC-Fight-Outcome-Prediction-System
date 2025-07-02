# UFC Fight Outcome Prediction System and Betting Value Checker

## Project Overview

This project builds a machine learning platform to predict UFC fight outcomes using fighter statistics, historical fight results, and live betting odds. It also scrapes live odds for upcoming fights to indentify value picks, and scrapes upcoming events to make predictions.

The prediction portion of the web app allows users to:
- Choose two valid fighters
- Predict the fight winner, outcome probabilities, and expected betting odds
- Compare predictions to live vegas odds to identify value picks

Predictions are generated in real-time through an ensemble of neural network models.

## Motivation

This idea came from my passion for the UFC and a curiosity: could I predict any possible fight outcome using machine learning? The project began as a basic stats dashboard in Pandas/Tableau, but evolved into a full ML pipeline once I started engineering features like ELO ratings, KO rates, and strength of competition. As an avid UFC fan, I combined my fight knowledge and technical skills to engineer these features and this model to create an intelligent, accurate and fun fight oucome predictor.

## Tech Stack + Achievements

- Stack: React, FastAPI, Docker, PyTorch, scikit-learn, BeautifulSoup
- Features: 50+ engineered stats, live odds scraping, full-stack web deployment
- Real-world success:
     - Winner Predictions: 60/78 (76.9%)
     - Outcome Predictions: 32/78 (41%)

## Key Features

- Predicts fight winners and detailed outcomes (KO, submission, decision) using neural network ensembles
- Integrates live Vegas odds and compares to model probabilities to highlight value betting opportunities
- Automates scraping of upcoming fights and generates weekly predictions
- Fully containerized backend (FastAPI + Docker) with modern React frontend (MUI-styled)


## Live Demo

https://mma-predictor.vercel.app/

## Project Structure

```
ufc-fight-outcome-prediction-system/
├── src/
|    ├── app_util.py              # Contains methods to assist app.py
|    ├── main.py                  # FastAPI root and /predict implementation
│    ├── fighter_predictions.py   # Prediction logic (model loading and odds handling)
│    ├── model.py                 # Neural network architecture and training functions
│    ├── feature_engineering.py   # Feature creation and transformation
│    ├── fighter_diffs.py         # Get individual fighter stats and prepare for retrieval from frontend
|    ├── scrape_odds.py           # Scraping odds from bestfightodds.com 
|    ├── scrape_event.py          # Scraping upcoming events and making predictions
|    └── data_cleaning.py         # Cleaning data for model training + individual stat retrieval
├── models/
│    ├── Known_Odds/              # Models trained with odds
│    ├── Unknown_Odds/            # Models trained without odds
│    ├── Predicting_Winner/       # Winner models (no odds)
│    └──Predicting_Winner_Odds/  # Winner models (with odds)
├── Data/
│    ├── Raw/                    # Original UFC data
│    │   ├── ufc-master.csv      # Main UFC fight history dataset
│    │   └── defense_data.csv    # Fighter defensive statistics
│    └── Cleaned/                # Cleaned data for model training
│        ├── fighter_stats.csv   # Individual fighter statistics
│        ├── odds_data.csv       # Betting odds data
│        └── ufc-clean.csv       # Cleaned and processed fight data
├── frontend/                    # React frontend
├── Dockerfile
├── requirements.txt
├── README.md
```
