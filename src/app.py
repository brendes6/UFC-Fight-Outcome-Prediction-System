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
     - Winner Predictions: 53/69 (76.8%)
     - Outcome Predictions: 29/69 (42%)
                
    ** UFC Fight Night: Hill v Rountree **
     - Winner Predictions: 3/6 (50%)
     - Outcome Predictions: 3/6 (50%)
                
    ** UFC Fight Night: Usman v Buckley **
     - Winner Predictions: 7/10 (70%)
     - Outcome Predictions: 5/10 (50%)
                
    ** UFC 316 **
     - Winner Predictions: 8/9 (89%)
     - Outcome Predictions: 3/9 (33%)
    
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
        ** Topuria vs Oliveira **
        - Predicted Winner: Ilia Topuria (68% confidence)
        - Predicted Outcome: Topuria KO/TKO (30.0%)
        - Value Pick: None
                
        ** Royval vs Van: **
        - Predicted Winner: Joshua Van (63% confidence)
        - Predicted Outcome: Van Decision (30.0%)
        - Value Pick: Van to win: Vegas says 48.8%, we say 62.7%. Kelly says bet 4.1% of your bankroll.       

        ** Dariush vs Moicano **
        - Predicted Winner: Renato Moicano (54% confidence)
        - Predicted Outcome: Moicano Decision (29.0%)
        - Value Pick: None     

        ** Talbott vs Lima **
        - Predicted Winner: Payton Talbott (62% confidence)
        - Predicted Outcome: Talbot KO/TKO (28.4%)
        - Value Pick: Talbott to win: Vegas says 40.0%, we say 61.9%. Kelly says bet 5.5% of your bankroll.       

        ** Amil vs Delgado **
        - Predicted Winner: Hyder Amil (53% confidence)
        - Predicted Outcome: Amil KO/TKO (36.2%)
        - Value Pick: Amil to win by KO/TKO: Vegas says 22.7%, we say 36.2%. Kelly says bet 2.6% of your bankroll.
        
        ** Hermansson vs Rodriguez **
        - Predicted Winner: Gregory Rodriguez (61% confidence)
        - Predicted Outcome: Rodriguez Decision (28.5%)
        - Value Pick: None
                        
        ** Araujo v Cortez: **
        - Predicted Winner: Tracy Cortez (65% confidence)
        - Predicted Outcome: Cortez Decision (59.1%)
        - Value Pick: None       
                
        ** McKinney v Borschev: **
        - Predicted Winner: Terrance McKinney (56% confidence)
        - Predicted Outcome: Borschev KO/TKO (24.0%)
        - Value Pick: Either fighter to win by decision: Vegas says 16.9%, we say 30.4%. Kelly says bet 2.4% of your bankroll.

        ** Price v Smith: **
        - Predicted Winner: Jacobe Smith (92% confidence)
        - Predicted Outcome: Smith KO/TKO (56.4%)
        - Value Pick: Smith to win by decision: Vegas says 13.3%, we say 24.7%. Kelly says bet 2.0% of your bankroll.        
        
                        
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
