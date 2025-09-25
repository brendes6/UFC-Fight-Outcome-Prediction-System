# UFC Fight Prediction & Analyics Platform

## Project Overview

This project is a machine learning and data engineering platform for predicting UFC fight outcomes using structured fighter statistics. It combines an automated data pipeline, a cloud-hosted prediction service, and a modern web frontend to deliver real-time fight analytics.

The platform supports:
- Predicting fight winners, outcome probabilities, and expected methods of victory
- Exploring fantasy matchups between any two fighters in the database
- Accessing continuously updated fighter stats and outcomes through a cloud-based pipeline

Predictions are generated through an ensemble of neural network models trained on 50+ handcrafted statistical features.

## Motivation

The project began as a simple stats dashboard in Pandas/Tableau, but grew into a full-scale ML system as I explored whether machine learning could reliably predict UFC fight outcomes. By engineering domain-specific features such as ELO ratings, striking efficiency, finish rates, and strength of competition, I built a predictive pipeline that balances technical rigor with my passion for MMA analytics.

## Tech Stack & Architecture

- Frontend: React (MUI-styled)
- Backend: FastAPI microservice, containerized with Docker
- Machine Learning: PyTorch, scikit-learn neural network ensembles
- Data Pipeline:
     - Scraper service deployed as a Google Cloud job (runs weekly post-events)
     - Google Cloud SQL database storing structured fighter stats for immediate prediction use
- Other: BeautifulSoup for scraping, REST APIs for serving predictions

## Real-World Performance

- Winner Predictions: 60/78 (76.9%)
- Outcome Predictions: 32/78 (41%)

## Key Features

- Predicts fight winners and outcome types (KO/TKO, submission, decision) in real-time
- Automates scraping and structuring of fighter stats with weekly updates to a cloud SQL database
- Provides a fantasy matchup simulator for any fighter pairing in the dataset
- Fully containerized deployment with a React frontend and FastAPI backend on GCP

## Live Demo

https://mma-predictor.vercel.app/