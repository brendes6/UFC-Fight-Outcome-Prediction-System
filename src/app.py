import streamlit as st
from fighter_predictions import predict_fight  
from app_util import get_all_fighters, implied_prob, get_weight_classes, get_odds_data, get_value_picks


st.title("UFC Fight Outcome Predictor and Betting Value Checker")


# Print the outcomes of the fight
def print_outcomes(red_fighter, blue_fighter, weight_class, betting_mode=False):

    # Get the odds data for the fight
    if betting_mode:
        odds_data = get_odds_data(red_fighter, blue_fighter)
        if any(i==None for i in odds_data.values()):
            betting_mode = False
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

    if odds_data:
        picks = get_value_picks(odds_data, mean_outcome_pred, mean_winner_pred)
    else:
        picks = []


    col1, col2, col3 = st.columns(3)
    
    # Print fight outcomes, checking for value on each outcome
    with col1:
        st.markdown(f"####  {red_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"* KO/TKO: {mean_outcome_pred[0]*100:.1f}% ({outcome_odds[0]})")
        st.markdown(f"* Submission: {mean_outcome_pred[1]*100:.1f}% ({outcome_odds[1]})")
        st.markdown(f"* Decision: {mean_outcome_pred[2]*100:.1f}% ({outcome_odds[2]})")
        
    with col2:
        st.markdown(f"####  {blue_fighter}")
        st.markdown(f"**Predicted Outcome:**")
        st.markdown(f"* KO/TKO: {mean_outcome_pred[3]*100:.1f}% ({outcome_odds[3]})")
        st.markdown(f"* Submission: {mean_outcome_pred[4]*100:.1f}% ({outcome_odds[4]})")
        st.markdown(f"* Decision: {mean_outcome_pred[5]*100:.1f}% ({outcome_odds[5]})")
    
    with col3:
        st.markdown(f"#### Value Picks:")
        if len(picks) == 0:
            st.markdown("No value picks found - full odds aren't available for this fight yet. Come back closer to fight day for value picks!")
        for pick in picks:
            st.markdown(pick)
        


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
    if not betting_mode:
        print_outcomes(red_fighter, blue_fighter, weight_class)
    else:
        print_outcomes(red_fighter, blue_fighter, weight_class, betting_mode=True)
