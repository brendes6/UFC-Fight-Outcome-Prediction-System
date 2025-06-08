import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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



if __name__ == "__main__":
    get_bfo_html()

