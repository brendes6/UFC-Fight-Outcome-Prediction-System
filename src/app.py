import streamlit as st
from fighter_predictions import predict_fight  

st.title("UFC Fight Outcome Predictor")

# Fighter inputs
red_fighter = st.text_input("Red Corner Fighter:")
blue_fighter = st.text_input("Blue Corner Fighter:")

# Option to use odds or not
use_odds = st.checkbox("Use Vegas Odds (if available)?", value=True)

if st.button("Predict Fight"):
    if red_fighter and blue_fighter:
        mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds, odds_available = predict_fight(red_fighter, blue_fighter, use_odds)


        if odds_available:
            st.write("Using Vegas Odds:")
        else:
            st.write("Using Unknown Odds:")
        st.write(f"\n\nPrediction: {red_fighter} vs {blue_fighter}\n")
        st.write(f"\tRed Wins:   {mean_winner_pred[0]*100:.1f}% ({winner_odds[0]})")
        st.write(f"\tBlue Wins:  {mean_winner_pred[1]*100:.1f}% ({winner_odds[1]})")
        st.write(f"\tRed KO:   {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
        st.write(f"\tRed Sub:  {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
        st.write(f"\tRed Dec:  {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
        st.write(f"\tBlue KO:  {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
        st.write(f"\tBlue Sub: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
        st.write(f"\tBlue Dec: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")

    else:
        st.error("Please enter both fighter names.")
