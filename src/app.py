import streamlit as st
from fighter_predictions import predict_fight  
from fighter_diffs import check_valid_fighter

st.title("UFC Fight Outcome Predictor")

# Fighter inputs
red_fighter = st.text_input("Red Corner Fighter:")
blue_fighter = st.text_input("Blue Corner Fighter:")

# Option to use odds or not
use_odds = st.checkbox("Use Vegas Odds (if available)?", value=False)

if st.button("Predict Fight"):
    if check_valid_fighter(red_fighter) and check_valid_fighter(blue_fighter):
        mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds, odds_available = predict_fight(red_fighter, blue_fighter, use_odds)


        if odds_available:
            st.write("Using Vegas Odds:")
        else:
            st.write("Using Unknown Odds:")
        st.markdown(f"###  {red_fighter} vs {blue_fighter}")
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"####  {red_fighter}")
            st.markdown(f"**Win Probability:** {mean_winner_pred[0]*100:.1f}% ({winner_odds[0]})")
            st.markdown(f"- KO/TKO: {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
            st.markdown(f"- Submission: {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
            st.markdown(f"- Decision: {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
            
        with col2:
            st.markdown(f"####  {blue_fighter}")
            st.markdown(f"**Win Probability:** {mean_winner_pred[1]*100:.1f}% ({winner_odds[1]})")
            st.markdown(f"- KO/TKO: {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
            st.markdown(f"- Submission: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
            st.markdown(f"- Decision: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")

    else:
        st.error("Please enter two valid fighter names.")
