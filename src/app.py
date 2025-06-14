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
     - Winner Predictions: 43/53 (81.1%)
     - Outcome Predictions: 21/53 (39.6%)
                
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
        ** Usman v Buckley: **
        - Predicted Winner: Joaquin Buckley (56% confidence)
        - Predicted Outcome: Buckley Decision (33.3%) 
        - Value Pick: Red to win by decision OR Blue to win by Submission: Vegas says 20.8%, we say 29.7%. (Rec. 1.7% bankroll)            

        ** Namajunas v Maverick: **
        - Predicted Winner: Rose Namajunas (61% confidence)
        - Predicted Outcome: Namajunas Decision (48.4%) 
        - Value Pick: None            

        ** Shahbazyan v Petroski: **
        - Predicted Winner: Andre Petroski (50% confidence)
        - Predicted Outcome: Petroski KO/TKO (20.5%) 
        - Value Pick: Red to win by submission OR Blue to win by KO: Vegas says 23.8%, we say 32.4%. (Rec. 1.7% bankroll)                 
                
        ** Garbrandt v Barcelos: **
        - Predicted Winner: Raoni Barcelos (58% confidence)
        - Predicted Outcome: Barcelos Decision (30.1%) 
        - Value Pick: Garbrandt to win: Vegas says 32.8%, we say 41.7%. (Rec. 2% bankroll)              

        ** Abdul-Malik v Brundage: **
        - Predicted Winner: Mansur Abdul-Malik (68% confidence)
        - Predicted Outcome: Abdul-Malik KO/TKO (38.3%) 
        - Value Pick: None      
                        
        ** Menifield v Sy: **
        - Predicted Winner: Oumar Sy (74% confidence)
        - Predicted Outcome: Sy Decision (28.3%) 
        - Value Pick: Menifield to win: Vegas says 16.9%, we say 25.6%. (Rec. 1.6% bankroll)                     
                
        ** Craig v Bellato: **
        - Predicted Winner: Rodolfo Bellato (75% confidence)
        - Predicted Outcome: Bellato KO/TKO (50.6%) 
        - Value Pick: None                       

        ** Chiesa v McGee: **
        - Predicted Winner: Michael Chiesa (75% confidence)
        - Predicted Outcome: Chiesa Decision (38.9%) 
        - Value Pick: None                       

        ** Simon v Smotherman: **
        - Predicted Winner: Ricky Simon (91% confidence)
        - Predicted Outcome: Simon Decision (53.5%) 
        - Value Pick: Simon to win by decision: Vegas says 37.7%, we say 53.5%. (Rec. 3.8% bankroll)            
        
        ** Rowe v Loosa: **
        - Predicted Winner: Phil Rowe (55% confidence)
        - Predicted Outcome: Rowe Decision (44.3%) 
        - Value Pick: Rowe to win by decision: Vegas says 26.7%, we say 44.3%. (Rec. 4.4% bankroll)          
        
        ** Horth v Demopoulos: **
        - Predicted Winner: Jamey-Lyn Horth (76% confidence)
        - Predicted Outcome: Horth Decision (55.4%) 
        - Value Pick: None               
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
