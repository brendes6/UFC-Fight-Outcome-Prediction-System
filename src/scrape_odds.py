import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from app_util import is_fighter
import pandas as pd
import os

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
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "odds-table"))
        )
        
        # Get the page source
        html = driver.page_source

        form_odds_df(html)

    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        try:
            driver.quit()
        except:
            pass
        





def form_odds_df(html):

    bs = BeautifulSoup(html, 'html.parser')


    rows = bs.find_all('tr')


    
    cols = ["Fighter", "Odds", "KOOdds", "SubOdds", "DecOdds"]
    
    df = pd.DataFrame(columns=cols)
    
    i = 0

    for i, row in enumerate(rows):
        name = row.text.split("+")[0].split("-")[0]

        if is_fighter(name.lower()):
            placeholder_data = dict.fromkeys(cols, None)

            placeholder_data["Fighter"] = name

            last_name = "".join(name.split(" ")[1:])

            try:
                props = int(row.text.split("\t")[-1].split(" ")[-1])
            except ValueError:
                props = 0

            for j in range(props):
                row = rows[i+j]
                # If the row contains the red fighter's name
                if row.text.find(last_name) > -1:
                    if row.text.find(f"{last_name} wins by TKO/KO+") > -1:
                        placeholder_data["KOOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name} wins by TKO/KO-") > -1:
                        placeholder_data["KOOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name} wins by submission+") > -1:
                        placeholder_data["SubOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name} wins by submission-") > -1:
                        placeholder_data["SubOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name} wins by decision+") > -1:
                        placeholder_data["DecOdds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name} wins by decision-") > -1:
                        placeholder_data["DecOdds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name}+") > -1:
                        placeholder_data["Odds"] = int(row.text.split("+")[1].split("-")[0].split("▲")[0].split("▼")[0])
                    elif row.text.find(f"{last_name}-") > -1:
                        placeholder_data["Odds"] = -1 * int(row.text.split("-")[1].split("+")[0].split("▲")[0].split("▼")[0])
            
            if props != 0:
                df = pd.concat([df, pd.DataFrame([placeholder_data])], ignore_index=True)
                    
            
    df.to_csv("../Data/Cleaned/odds_data.csv")


if __name__ == "__main__":
    get_bfo_html()

