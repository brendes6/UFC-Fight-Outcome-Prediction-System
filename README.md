# UFC Fight Prediction & Analytics Platform

## Project Overview

This project is a machine learning and data engineering platform for predicting UFC fight outcomes using structured fighter statistics. It combines an automated data pipeline, a trained neural network model, and a modern web frontend to deliver fight outcome predictions and analytics.

The platform supports:
- Predicting fight winners with outcome probabilities and expected methods of victory
- Exploring fantasy matchups between any two fighters in the database
- Accessing continuously updated fighter stats through an automated cloud-based pipeline

Predictions are generated through a PyTorch neural network trained on 50+ handcrafted statistical features including ELO ratings, momentum indicators, striking efficiency, and strength of schedule.

## Motivation

The project began as a simple stats dashboard in Pandas/Tableau, but evolved into a full-scale ML system as I explored whether machine learning could reliably predict UFC fight outcomes. By engineering domain-specific features such as ELO ratings, striking efficiency, finish rates, and strength of competition, I built a predictive pipeline that balances technical rigor with my passion for MMA analytics.

## Tech Stack & Architecture

**Frontend:** React, deployed on Vercel  
**Backend:** FastAPI microservice, containerized with Docker  
**Machine Learning:** PyTorch neural network ensemble, scikit-learn  
**Data Pipeline:**
- Automated scraper service (BeautifulSoup) deployed as scheduled Cloud Run job
- Runs weekly post-UFC events to update fighter statistics
- Google Cloud SQL database storing structured fighter stats and historical fight data
**Deployment:** Initially deployed on GCP Vertex AI with TorchServe; current demo uses cached predictions due to cost optimization for portfolio project. Full codebase available in repository.

## Real-World Performance

Validated on 75+ real UFC fights (unseen during training):
- **Winner Predictions:** 60/78 correct (76.9% accuracy)
- **Outcome Type Predictions:** 32/78 correct (41.0% accuracy)


## Key Features

- **Real-time Predictions:** Generates fight winner probabilities and expected finish methods
- **Automated Data Pipeline:** Weekly scraping and feature engineering of fighter statistics with cloud-based storage
- **Fantasy Matchup Simulator:** Predict outcomes for any hypothetical fighter pairing in the database
- **Production Architecture:** Containerized microservices with REST API, demonstrating end-to-end ML deployment

## Technical Highlights

- **Feature Engineering:** 50+ custom features including momentum indicators, career trajectory metrics, and opponent-adjusted statistics
- **Model Architecture:** Ensemble of neural networks with dropout regularization and cross-validation
- **Deployment Strategy:** Explored production ML serving (Vertex AI/TorchServe) and optimized for cost-effective alternatives (Cloud Run with in-container inference)
- **Scalability Considerations:** Designed data pipeline to handle incremental updates; model serving optimized for low-latency inference (<300ms average response time)


## Current Deployment Status

**Update as of October 2025:**  
The initial production deployment used GCP Vertex AI with TorchServe for model serving (~$150/month). For portfolio demonstration purposes, the live demo currently shows cached prediction results while the full source code and trained models remain available in the repository. 

In a production scenario with real users, cost optimization strategies would include:
- Cloud Run deployment with model loaded in-container (pay-per-request pricing)
- Request batching to amortize compute costs
- Model quantization to reduce inference latency
- Spot instances for cost-effective compute

The current demo showcases the full technical architecture and prediction capabilities through cached results.

## Live Demo

**Frontend:** https://mma-predictor.vercel.app/  