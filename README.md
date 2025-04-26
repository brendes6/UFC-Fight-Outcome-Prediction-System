# UFC Fight Outcome Prediction System

A machine learning system that predicts UFC fight outcomes using fighter statistics and historical data.
In fighter_predictions.py, you can enter any 2 currently rostered fighters to get a prediction on their fight outcome.

## Project Structure

- `src/`: Contains the main Python source code
  - `data_cleaning.py`: Data preprocessing and cleaning
  - `feature_engineering.py`: Feature extraction and transformation
  - `model.py`: Neural network model implementation
  - `fighter_diffs.py`: Fighter statistics comparison
  - `fighter_predictions.py`: Main prediction interface
- `Models/`: Trained model files
- `Data/`: UFC fight data

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The system can be used to predict UFC fight outcomes by comparing fighter statistics and historical performance.

## Dependencies

- Python 3.8+
- See requirements.txt for package dependencies