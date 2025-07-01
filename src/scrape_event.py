import requests
from bs4 import BeautifulSoup
import pandas as pd


def get_upcoming_predictions():


    response = requests.get('https://www.ufc.com/events')

    bs = BeautifulSoup(response.content, "html.parser")

    rows = bs.find_all("a", href=True)

    for row in rows:
        href = row['href']

        if "event/ufc-" in href:
            url = href
            break

    response = requests.get(url)
    bs = BeautifulSoup(response.content, "html.parser")
    rows = bs.find_all("a")

    first_names = []
    last_names = []

    for row in rows:
        rows2 = row.find_all("span")
        for row2 in rows2:
            if row2.has_attr("class"):
                if row2["class"][0] == "c-listing-fight__corner-given-name":
                    first_names.append(row2.text)
                elif row2["class"][0] == "c-listing-fight__corner-family-name":
                    last_names.append(row2.text)

    fights = []

    for i in range(0, len(first_names), 2):
        fights.append((first_names[i] + " " + last_names[i], first_names[i+1] + " " + last_names[i+1]))

    cols=["fighter1", "fighter2", "Red to Win",
                    "Blue to Win", "Red by KO", "Red by Sub", "Red by Dec",
                    "Blue by KO", "Blue by Sub", "Blue by Dec", "value_picks"]
    
    outcomes = ["Red to Win",
                    "Blue to Win", "Red by KO", "Red by Sub", "Red by Dec",
                    "Blue by KO", "Blue by Sub", "Blue by Dec"]
    
    data = {col: [] for col in cols}

    
    for fight in fights:

        pars = {"fighter1": fight[0], "fighter2":fight[1]}

        response = requests.get("https://ufc-predictor.fly.dev/predict", params=pars)

        jsn = response.json()

        if "predicted_probs" in jsn:
            for outcome in outcomes:
                data[outcome].append(f"{jsn['predicted_probs'][outcome]:.2f}")

            data["value_picks"].append(jsn["value_picks"])
            data["fighter1"].append(fight[0])
            data["fighter2"].append(fight[1])

    
    df = pd.DataFrame(data=data)

    df.to_csv("../Data/Cleaned/upcoming.csv")


if __name__ == "__main__":
    get_upcoming_predictions()
                                

