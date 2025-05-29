# Convert American odds to implied probability
def implied_prob(american_odds):
    if american_odds > 0:
        return 100 / (american_odds + 100)
    else:
        return -american_odds / (-american_odds + 100)


def odds_conversion(predictions):
    # Convert percentage predictions to odds

    odds = []

    for prediction in predictions:
        if prediction == 0.5:
            odds.append("+100")
        elif prediction < 0.5:
            odds.append(f"+{(int(((1 - prediction) / prediction) * 100) // 10) * 10:.0f}")
        else:
            odds.append(f"{(int((-prediction / (1 - prediction)) * 100) // 10) * 10:.0f}")

    return odds
