import streamlit as st
from fighter_predictions import predict_fight  
from fighter_diffs import check_valid_fighter, get_all_fighters, get_random_fighter
import random
st.title("UFC Fight Outcome Predictor")

def implied_prob(american_odds):
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return -american_odds / (-american_odds + 100)

def get_weight_classes(gender):
    if gender == "Female":
        return ["All", "Strawweight", "Flyweight", "Bantamweight"]
    else:
        return ["All", "Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
    
def print_outcomes(red_fighter, blue_fighter, use_odds, weight_class):
    mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds, odds_available, odds = predict_fight(red_fighter, blue_fighter, use_odds)

    if odds_available and use_odds:
        st.write("Using Model Trained on Known Odds:")
    elif not odds_available and use_odds:
        st.write("No Odds Available - Using Default Model")
    else:
        st.write("Using Default Model (Unknown Odds)")
    st.markdown(f"###  {red_fighter} vs {blue_fighter}")
    st.markdown(f"**Weight Class:** {weight_class}")
    st.markdown("---")
    st.markdown("#### Predicted Winner")
    if mean_winner_pred[0] > mean_winner_pred[1]:
        st.markdown(f"##### {red_fighter} ({mean_winner_pred[0]*100:.0f}% confidence)")
    else:
        st.markdown(f"##### {blue_fighter} ({mean_winner_pred[1]*100:.0f}% confidence)")
    st.markdown("---")
    
    if odds_available and use_odds:
        st.markdown("#### Value Checking")
        st.markdown(f"**Vegas Odds:** {odds[0]}, {odds[1]}")
        st.markdown(f"**Predicted Odds:** {winner_odds[0]}, {winner_odds[1]}")
        my_red_implied, my_blue_implied = implied_prob(int(winner_odds[0])), implied_prob(int(winner_odds[1]))
        vegas_red_implied, vegas_blue_implied = implied_prob(int(odds[0])), implied_prob(int(odds[1]))
        if my_red_implied > vegas_red_implied:
            st.markdown(f"Value detected on {red_fighter} (Model: {my_red_implied:.0%} vs Market: {vegas_red_implied:.0%})")
        if my_blue_implied > vegas_blue_implied:
            st.markdown(f"Value detected on {blue_fighter} (Model: {my_blue_implied:.0%} vs Market: {vegas_blue_implied:.0%})")

        st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"####  {red_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"- KO/TKO: {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
        st.markdown(f"- Submission: {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
        st.markdown(f"- Decision: {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
        
    with col2:
        st.markdown(f"####  {blue_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"- KO/TKO: {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
        st.markdown(f"- Submission: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
        st.markdown(f"- Decision: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")

with st.sidebar.expander("ℹ️ How it Works"):
    st.markdown("""
    This app uses an ensemble of machine learning models trained on historical UFC data to predict:

    - The most likely winner of a given fight
    - Probabilities of each fighter winning by KO/TKO, submission, or decision
    - Betting value based on the model's predicted win percentage vs Vegas odds

    You can:
    - Choose gender + weight class
    - Select any two valid fighters
    - Use real-time Vegas odds (when available) or default to stat-only models
    - Generate predictions instantly, including value picks and odds estimates
    """)


gender = st.selectbox("Gender:", ["Male", "Female"], index=None, placeholder="Select a gender")

weight_class = st.selectbox("Weight Class:", get_weight_classes(gender), index=None, placeholder="Select a weight class")
st.write("Note: Predictions across weight classes / genders will not be as accurate.")

# Fighter inputs
red_fighter = st.selectbox("Red Corner Fighter:", get_all_fighters(weight_class, gender), index=None, placeholder="Select a fighter",)
blue_fighter = st.selectbox("Blue Corner Fighter:", get_all_fighters(weight_class, gender), index=None, placeholder="Select a fighter")

# Option to use odds or not
use_odds = st.checkbox("Use Vegas Odds (if available)?", value=False)

if st.button("Predict Fight"):
    if check_valid_fighter(red_fighter) and check_valid_fighter(blue_fighter):
        print_outcomes(red_fighter, blue_fighter, use_odds, weight_class)
    else:
        st.error("Please enter two valid fighter names.")

if st.button("Predict Random Fight"):
    random_weight_class = get_weight_classes("Male")[random.randint(0, len(get_weight_classes("Male")) - 1)]
    red_fighter = get_random_fighter(random_weight_class, "Male")
    blue_fighter = get_random_fighter(random_weight_class, "Male")
    while red_fighter == blue_fighter:
        blue_fighter = get_random_fighter(random_weight_class, "Male")
    print_outcomes(red_fighter, blue_fighter, use_odds, random_weight_class)
