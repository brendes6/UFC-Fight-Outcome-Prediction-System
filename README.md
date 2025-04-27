# UFC Fight Outcome Prediction System

A machine learning system that predicts UFC fight outcomes using fighter statistics and historical data. The system includes both a Python interface and a web application for making predictions.

## Project Structure

- `src/`: Contains the main Python source code
  - `data_cleaning.py`: Data preprocessing and cleaning
  - `feature_engineering.py`: Feature extraction and transformation
  - `model.py`: Neural network model implementation
  - `fighter_diffs.py`: Fighter statistics comparison
  - `fighter_predictions.py`: Main prediction interface
  - `get_odds.py`: UFC odds retrieval functionality
  - `app.py`: Web application interface
- `Models/`: Trained model files
- `Data/`: UFC fight data

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Python Interface
Run predictions directly using the Python interface:
```bash
python src/fighter_predictions.py
```

### Web Interface
You can access the application in two ways:

1. **Local Deployment**
   Start the web application:
   ```bash
   python src/app.py
   ```
   Then open your browser to the provided local URL (typically http://127.0.0.1:5000)

2. **Web Deployment**
   The application is deployed using Streamlit and can be accessed at:
   https://ufc-fight-outcome-prediction-system-af9azviwjgntmxb2wkcv8b.streamlit.app/

## Dependencies

- Python 3.8+
- See requirements.txt for package dependencies