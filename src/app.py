import streamlit as st
from fighter_predictions import predict_fight  
from fighter_diffs import check_valid_fighter, get_all_fighters, get_random_fighter
from scrape_odds import get_odds_data
import random
from odds_util import implied_prob


st.title("UFC Fight Outcome Predictor and Betting Value Checker")


# Get weight classes for the selected gender
def get_weight_classes(gender):
    if gender == "Female":
        return ["All", "Strawweight", "Flyweight", "Bantamweight"]
    else:
        return ["All", "Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"]
    
# Print the outcomes of the fight
def print_outcomes(red_fighter, blue_fighter, weight_class, betting_mode=False):

    # Get the odds data for the fight
    if betting_mode:
        odds_data = get_odds_data(red_fighter, blue_fighter)
        if any(i==None for i in odds_data.values()):
            betting_mode = False
            st.markdown("### No ML/outcome odds found. Using default predictive model.")
            odds_data = None
    else:
        odds_data = None

    # Get the predictions for the fight
    mean_outcome_pred, mean_winner_pred, outcome_odds, winner_odds = predict_fight(red_fighter, blue_fighter, odds_data=odds_data)

    # Print the outcomes of the fight
    st.markdown(f"###  {red_fighter} vs {blue_fighter}")
    st.markdown(f"**Weight Class:** {weight_class}")
    st.markdown("---")
    st.markdown("#### Predicted Winner")
    if mean_winner_pred[0] > mean_winner_pred[1]:
        st.markdown(f"##### {red_fighter} ({mean_winner_pred[0]*100:.0f}% confidence)")
    else:
        st.markdown(f"##### {blue_fighter} ({mean_winner_pred[1]*100:.0f}% confidence)")
    st.markdown("---")

    mean_outcome_pred = [
        mean_outcome_pred[0],
        mean_outcome_pred[1],
        mean_outcome_pred[2],
        mean_outcome_pred[3],
        mean_outcome_pred[4],
        mean_outcome_pred[5],
        mean_outcome_pred[0] + mean_outcome_pred[3],
        mean_outcome_pred[1] + mean_outcome_pred[4],
        mean_outcome_pred[2] + mean_outcome_pred[5],
    ]

    # List of odds to check, list to store betting value
    values = ["RedOdds", "BlueOdds", "RedKOOdds", "RedSubOdds", "RedDecOdds", "BlueKOOdds", "BlueSubOdds", "BlueDecOdds", "EitherKOOdds", "EitherSubOdds", "EitherDecOdds"]
    betting_value = [None, None, None, None, None, None, None, None, None]

    # If betting mode is enabled, check for value
    if betting_mode:
        st.markdown("#### Moneyline Value Checking")
        st.markdown(f"**Vegas Odds:** {odds_data[values[0]]}, {odds_data[values[1]]}")
        st.markdown(f"**Predicted Odds:** {winner_odds[0]}, {winner_odds[1]}")
        my_red_implied, my_blue_implied = mean_winner_pred[0], mean_winner_pred[1]
        vegas_red_implied, vegas_blue_implied = implied_prob(int(odds_data[values[0]])), implied_prob(int(odds_data[values[1]]))
        if my_red_implied > vegas_red_implied:
            st.markdown(f"Value detected on {red_fighter} (Model: {my_red_implied:.0%} vs Market: {vegas_red_implied:.0%})")
        if my_blue_implied > vegas_blue_implied:
            st.markdown(f"Value detected on {blue_fighter} (Model: {my_blue_implied:.0%} vs Market: {vegas_blue_implied:.0%})")

        st.markdown("---")

        # Check for value on each outcome
        for i in range(9):
            vegas_implied = implied_prob(int(odds_data[values[i+2]]))
            if mean_outcome_pred[i]  - vegas_implied > 0.02:
                betting_value[i] = vegas_implied
    
    
    col1, col2, col3 = st.columns(3)
    
    # Print fight outcomes, checking for value on each outcome
    with col1:
        st.markdown(f"####  {red_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"* KO/TKO: {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
        if betting_value[0] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[0]*100:.1f}%")
        st.markdown(f"* Submission: {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
        if betting_value[1] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[1]*100:.1f}%")
        st.markdown(f"* Decision: {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
        if betting_value[2] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[2]*100:.1f}%")
        
    with col2:
        st.markdown(f"####  {blue_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"* KO/TKO: {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
        if betting_value[3] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[3]*100:.1f}%")
        st.markdown(f"* Submission: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
        if betting_value[4] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[4]*100:.1f}%")
        st.markdown(f"* Decision: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")
        if betting_value[5] != None:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp; ✅ Value detected: Vegas says {betting_value[5]*100:.1f}%")
    
    with col3:
        st.markdown(f"#### General Fight Outcome Value")
        if betting_value[6] != None:
            st.markdown(f"✅ Value detected on Fight outcome being KO/TKO: Vegas says {betting_value[6]*100:.1f}%, we say {mean_outcome_pred[6]*100:.1f}%")
        if betting_value[7] != None:
            st.markdown(f"✅ Value detected on Fight outcome being Submission: Vegas says {betting_value[7]*100:.1f}%, we say {mean_outcome_pred[7]*100:.1f}%")
        if betting_value[8] != None:
            st.markdown(f"✅ Value detected on Fight outcome being Decision: Vegas says {betting_value[8]*100:.1f}%, we say {mean_outcome_pred[8]*100:.1f}%")

with st.sidebar.expander("How it Works"):
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

with st.sidebar.expander("Recent Accuracy Tracker"):
    st.markdown("""
    **Fights since Apr 10:**
     - Winner Predictions: 35/44 (79.5%)
     - Outcome Predictions: 18/44 (40.9%)
    
    ** UFC ON ESPN: Blanchfield v Barber**
     - Winner Predictions: 5/7 (71%)
     - Outcome Predictions: 3/7 (43%)
                
    **UFC Fight Night: Burns v Morales**
     - Winner Predictions: 6/6 (100%)
     - Outcome Predictions: 2/6 (33%)
        
    **UFC 315:**
     - Winner Predictions: 5/8 (62%)
     - Outcome Predictions: 3/8 (38%))

    **UFC Fight Night: Sandhagen v Figueiredo**
     - Winner Predictions: 6/6 (100%)
     - Outcome Predictions: 3/6 (50%)
                
    **UFC ON ESPN: Garry vs Prates**:
     - Winner Predictions: 8/10 (80%)
     - Outcome Predictions: 4/10 (40%)
                
    **UFC 314**:
     - Winner Predictions: 5/7 (71%)
     - Outcome Predictions: 3/7 (43%)
    """)

with st.sidebar.expander("Upcoming Fight Predictions"):
    st.markdown("""
        ** Dvalishvili v O'Malley: **
        - Predicted Winner: Merab Dvalishvili (56% confidence)
        - Predicted Outcome: Dvalishvili Decision (29.6%) 
        - Value Picks: O'Malley ML (We say 44%, Vegas says 29%), Fight outcome being Submission (We say 30.5%, Vegas says 14.5%)
                
        ** Pena v Harrison: **
        - Predicted Winner: Kayla Harrison (70% confidence)
        - Predicted Outcome: Harrison Decision (31.9%) 
        - Value Pick: Pena ML (We say 30%, Vegas says 18%)
                
        ** Gastelum v Pyfer: **
        - Predicted Winner: Joe Pyfer (72% confidence)
        - Predicted Outcome: Pyfer Decision (30.7%) 
        - Value Pick: None
                
        ** Holland v Luque: **
        - Predicted Winner: Kevin Holland (57% confidence)
        - Predicted Outcome: Holland Decision (26.5%) 
        - Value Pick: Luque ML (We say 43%, Vegas says 36%)
                
        ** Silva v Van: **
        - Predicted Winner: Joshua Van (75% confidence)
        - Predicted Outcome: Van Decision (31.6%) 
        - Value Pick: None

        ** Murzakanov v Ribeiro: **
        - Predicted Winner: Azamat Murzakanov (80% confidence)
        - Predicted Outcome: Murzakanov KO/TKO (43.1%) 
        - Value Pick: Murzakanov Decision (We say 25.6%, Vegas says 14.3%)

        ** Spivak v Cortes-Acosta: **
        - Predicted Winner: Sergey Spivak (60% confidence)
        - Predicted Outcome: Spivak Decision (26.7%) 
        - Value Pick: Spivak KO/TKO (We say 21.1%, Vegas says 15.4%)
                
        ** Lipski v Cong: **
        - Predicted Winner: Wang Kong (73% confidence)
        - Predicted Outcome: Kong KO/TKO (30.4%) 
        - Value Pick: Lipski KO/TKO (We say 13.3%, Vegas says 6.2%)                
        
        ** Salkilld v Ashmouz: **
        - Predicted Winner: Quillian Salkilld (92% confidence)
        - Predicted Outcome: Salkilld Decision (34.8%) 
        - Value Picks: Salkilld KO/TKO (We say 30.2%, Vegas says 18.2%), Salkilld ML (We say 92%, Vegas says 80%)
""")

gender = st.selectbox("Gender:", ["Male", "Female"], index=None, placeholder="Select a gender")

weight_class = st.selectbox("Weight Class:", get_weight_classes(gender), index=None, placeholder="Select a weight class")
st.write("Note: Predictions across weight classes / genders will not be as accurate.")

# Fighter inputs
red_fighter = st.selectbox("Red Corner Fighter:", get_all_fighters(weight_class, gender), index=None, placeholder="Select a fighter",)
blue_fighter = st.selectbox("Blue Corner Fighter:", get_all_fighters(weight_class, gender), index=None, placeholder="Select a fighter")

# Option to use betting mode or not
betting_mode = st.toggle("Sports Betting Value Mode", value=False)
st.markdown("Sports Betting Value Mode compares our model's predictions to Vegas odds to find value picks.")

if st.button("Predict Fight"):
    if check_valid_fighter(red_fighter) and check_valid_fighter(blue_fighter):
        if not betting_mode:
            print_outcomes(red_fighter, blue_fighter, weight_class)
        else:
            print_outcomes(red_fighter, blue_fighter, weight_class, betting_mode=True)
    else:
        st.error("Please enter two valid fighter names.")

if st.button("Predict Random Fight"):
    random_weight_class = get_weight_classes("Male")[random.randint(0, len(get_weight_classes("Male")) - 1)]
    red_fighter = get_random_fighter(random_weight_class, "Male")
    blue_fighter = get_random_fighter(random_weight_class, "Male")
    while red_fighter == blue_fighter:
        blue_fighter = get_random_fighter(random_weight_class, "Male")
    print_outcomes(red_fighter, blue_fighter, random_weight_class)
