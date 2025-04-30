# UFC Fight Outcome Prediction System

## Project Overview

This project builds a machine learning platform to predict UFC fight outcomes using fighter statistics, historical fight results, and live betting odds.

The web app allows users to:
- Select gender and weight class
- Choose two valid fighters
- Predict the fight winner, outcome probabilities, and expected betting odds

Predictions are generated in real-time through an ensemble of neural network models.

## Key Features

- **Winner Prediction**: Predicts the overall fight winner with confidence percentage
- **Fight Outcome Prediction**: Predicts probabilities for KO/TKO, Submission, or Decision for each fighter
- **Live Odds Integration**: Incorporates current moneyline odds when available
- **Dynamic Fighter Selection**: Filters fighters by gender and weight class for valid matchups
- **Responsive Web App**: Built with Streamlit for fast interaction and real-time updates

## Machine Learning Details

- **Models**: Ensembles of 6 neural networks per task (outcome prediction and winner prediction)
- **Training**: Stratified cross-validation and early stopping based on validation accuracy
- **Validation Accuracy**:
  - Fight Outcome (6-class): 40–42%
  - Winner Prediction (binary): 70–71%
- **Features**: Over 50 engineered features based on:
  - Striking and grappling statistics
  - Submission attempt rates
  - Historical win/loss data
  - ELO ratings
  - Betting market data

## Live Demo

https://ufc-predictor-brendes6.streamlit.app/

## Project Structure

```
ufc-fight-outcome-prediction-system/
├── src/
│    ├── app.py                  # Streamlit app frontend
│    ├── fighter_predictions.py   # Prediction logic (model loading and odds handling)
│    ├── model.py                 # Neural network architecture and training functions
│    ├── feature_engineering.py   # Feature creation and transformation
│    ├── fighter_diffs.py         # Get individual fighter stats and prepare for retreival from frontend
|    ├── get_odds.py              # Pulling odds from API
|    └── data_cleaning.py         # Cleaning data for model training + individual stat retreival
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
│        └── ufc-clean.csv       # Cleaned and processed fight data
├── requirements.txt
├── README.md
```

## Future Plans

- Predict full fight cards at once
- Add value bet screening (based on model odds vs market odds)
- Track simulated bankroll performance over historical data
- Add real-time event scraping for upcoming UFC cards
- Continue improving model calibration and confidence estimation

