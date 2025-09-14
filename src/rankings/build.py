from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd

year = 2025

def get_schedule():

    url = f"https://www.sports-reference.com/cfb/years/{year}-schedule.html"

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="schedule")
    driver.quit()

    headers = []
    thead = table.find_next("thead")
    for th in thead.find_all("th"):
        headers.append(th.text.strip())

    rows = []
    for tr in table.find_all("tr"):
        cells = [td.text.strip() for td in tr.find_all("td")]
        if cells: # Only add rows that contain data cells (skip header row if already processed)
            rows.append(cells)

    df = pd.DataFrame(rows, columns=headers[1:])  # Exclude the first header "Rk"

    # Sanitize team names to get rid of ranking
    for col in ["Winner", "Loser"]:
        if col in df.columns:
            df[col] = df[col].str.replace(r"\(\d+\)", "", regex=True)

    print(df)

def main():
    get_schedule()


if __name__ == "__main__":
    main()
