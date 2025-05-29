import pandas as pd
from bs4 import BeautifulSoup
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from odds_util import implied_prob, odds_conversion

URL = "https://www.bestfightodds.com/"

def get_bfo_html():

    # Options for the driver to prevent 403
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')

    try:
        # Initialize the Chrome driver
        driver = webdriver.Chrome(options=chrome_options)
        
        # Wait for 4 seconds
        time.sleep(4)

        # Get the HTML of the page
        driver.get(URL)
        
        # Wait for the table to be present
        print("Waiting for content to load...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "odds-table"))
        )
        
        # Get the page source
        html = driver.page_source

        # Save the HTML to a file
        with open('../html_files/odds_file.html', 'w', encoding='utf-8') as f:
            f.write(html)

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        try:
            driver.quit()
        except:
            pass


def get_odds_data(red_fighter, blue_fighter):
    with open('../html_files/odds_file.html', 'r', encoding='utf-8') as f:
        html = f.read()

    bs = BeautifulSoup(html, 'html.parser')

    rows = bs.find_all('tr')

    odds = {
        "RedOdds": None,
        "BlueOdds": None,
        "RedSubOdds": None,
        "BlueSubOdds": None,
        "RedKOOdds": None,
        "BlueKOOdds": None,
        "RedDecOdds": None,
        "BlueDecOdds": None,
    }

    # Fighters last names
    red_fighter_name = red_fighter.split(" ")[1]
    blue_fighter_name = blue_fighter.split(" ")[1]


    for row in rows:
        # If the row contains the red fighter's name
        if row.text.find(red_fighter_name) > -1:
            if row.text.find(f"{red_fighter_name} wins by TKO/KO+") > -1:
                odds["RedKOOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by TKO/KO-") > -1:
                odds["RedKOOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by submission+") > -1:
                odds["RedSubOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by submission-") > -1:
                odds["RedSubOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by decision+") > -1:
                odds["RedDecOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name} wins by decision-") > -1:
                odds["RedDecOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name}+") > -1:
                odds["RedOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{red_fighter_name}-") > -1:
                odds["RedOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
        # If the row contains the blue fighter's name
        elif row.text.find(blue_fighter_name) > -1:
            if row.text.find(f"{blue_fighter_name} wins by TKO/KO+") > -1:
                odds["BlueKOOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by TKO/KO-") > -1:
                odds["BlueKOOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by submission+") > -1:
                odds["BlueSubOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by submission-") > -1:
                odds["BlueSubOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by decision+") > -1:
                odds["BlueDecOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name} wins by decision-") > -1:
                odds["BlueDecOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name}+") > -1:
                odds["BlueOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
            elif row.text.find(f"{blue_fighter_name}-") > -1:
                odds["BlueOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])

    # If we have odds, calculat the 'either ...' odds
    if all(value != None for value in odds.values()):
        odds["EitherSubOdds"] = odds_conversion([implied_prob(odds["RedSubOdds"]) + implied_prob(odds["BlueSubOdds"])])[0]
        odds["EitherKOOdds"] = odds_conversion([implied_prob(odds["RedKOOdds"]) + implied_prob(odds["BlueKOOdds"])])[0]
        odds["EitherDecOdds"] = odds_conversion([implied_prob(odds["RedDecOdds"]) + implied_prob(odds["BlueDecOdds"])])[0]

    return odds



if __name__ == "__main__":
    print(get_odds_data("Erin Blanchfield", "Maycee Barber"))

