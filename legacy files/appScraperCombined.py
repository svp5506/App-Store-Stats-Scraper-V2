from bs4 import BeautifulSoup
import requests
import json
from datetime import date, datetime
import pandas as pd
import sqlite3
from urls import urlIOS, urlAndroid
from appKey import keyIOS, keyAndroid

# Access Database
conn = sqlite3.connect("Database/app_store_stats.db")
cursor = conn.cursor()


# Scrape iOS App Store Data
def scrapeDataIOS(urlIOS):
    result = requests.get(urlIOS)
    parse = BeautifulSoup(result.content, "lxml")
    script = parse.find(type="application/ld+json").text.strip()
    data = json.loads(script)

    # Retrieve and format App rank if available
    rank_element = parse.find("a", {"class": "inline-list__item"})
    rank = None
    if rank_element is not None:
        rank_text = rank_element.text.strip().split()[0]
        rank = int(rank_text.replace(",", "").replace("#", ""))

    # Retrieve App Rating and Review Count
    app_rating = None
    review_count = None
    if "aggregateRating" in data:
        app_rating = data["aggregateRating"].get("ratingValue")
        review_count = data["aggregateRating"].get("reviewCount")

    # Create columns for each field
    dataApp = {
        "App Name": data.get("name"),
        "iOS App Rating": app_rating,
        "iOS Total Reviews": review_count,
        "iOS Rank": rank,
    }
    return dataApp


# Append each new URL data with existing data
dataIOS = []
for link in urlIOS:
    dataApp = scrapeDataIOS(link)
    dataIOS.append(dataApp)

# Convert to dataframe and merge with keyIOS (unique ID for each app)
dataIOS = pd.DataFrame(dataIOS)
dataIOS = pd.merge(dataIOS, keyIOS, on="App Name", how="outer")
dataIOS.set_index("Mapping", inplace=True)

# Add timestamps
now = datetime.now()
dataIOS.insert(0, "Timestamp", now.strftime("%Y-%m-%d %H:%M:%S"))
dataIOS.insert(0, "Date", now.strftime("%B %d, %Y"))


# Scrape Android App Store Data
def scrapeDataAndroid(urlAndroid):
    result = requests.get(urlAndroid)
    parse = BeautifulSoup(result.content, "lxml")

    # Get Star Rating
    starRatingRaw = parse.find("div", {"class": "TT9eCd"})
    if starRatingRaw is not None:
        starRating = starRatingRaw.text.replace("star", "")
    else:
        starRating = ""

    # Get App Name
    appName = parse.find("h1", {"itemprop": "name"}).text

    temp_list = [None] * 9
    temp_list[0] = datetime.now().strftime("%B %d, %Y")  # Date
    temp_list[6] = starRating  # Star Rating
    temp_list[7] = appName  # App Name
    temp_list[8] = now.strftime("%Y-%m-%d %H:%M:%S")  # Timestamp

    divReviews = parse.find_all("div", {"class": "RutFAf wcB8se"})
    if divReviews:
        for i, div in enumerate(divReviews):
            countReviewsRaw = div["title"]
            countReviews = countReviewsRaw.replace(",", "")
            temp_list[i + 1] = int(countReviews)
    return temp_list


dataAndroid = []
for link in urlAndroid:
    temp_list = scrapeDataAndroid(link)
    dataAndroid.append(temp_list)

dataAndroid = pd.DataFrame(
    dataAndroid,
    columns=[
        "Date",
        "5 Star Reviews",
        "4 Star Reviews",
        "3 Star Reviews",
        "2 Star Reviews",
        "1 Star Reviews",
        "Android App Rating",
        "App Name",
        "Timestamp",
    ],
)

dataAndroid["Android Total Reviews"] = dataAndroid[
    [
        "5 Star Reviews",
        "4 Star Reviews",
        "3 Star Reviews",
        "2 Star Reviews",
        "1 Star Reviews",
    ]
].sum(axis=1)

dataAndroid = pd.merge(
    dataAndroid, keyAndroid, on="App Name", how="outer", suffixes=("_left", "_right")
)
dataAndroid.set_index("Mapping", inplace=True)


# Check for duplicate iOS data, App Data should exist for only one instance per day
today = date.today().strftime("%Y-%m-%d")
dataIOS = dataIOS[dataIOS["Timestamp"].str.startswith(today)].copy()
cursor.execute(f"SELECT * FROM tableIOS WHERE [Date] = '{now.strftime('%B %d, %Y')}'")
existing_data = cursor.fetchall()
if existing_data:
    cursor.execute(f"DELETE FROM tableIOS WHERE [Date] = '{now.strftime('%B %d, %Y')}'")
    conn.commit()

# Add data to iOS Table if unique
dataIOS.to_sql("tableIOS", conn, if_exists="append", index=True)
conn.commit()

# Check for duplicate Android data, App Data should exist for only one instance per day
dataAndroid = dataAndroid[dataAndroid["Timestamp"].str.startswith(today)].copy()
cursor.execute(
    f"SELECT * FROM tableAndroid WHERE [Date] = '{now.strftime('%B %d, %Y')}'"
)
existing_data_Android = cursor.fetchall()
if existing_data_Android:
    cursor.execute(
        f"DELETE FROM tableAndroid WHERE [Date] = '{now.strftime('%B %d, %Y')}'"
    )
    conn.commit()

# Add data to Anbdroid Table if unique
dataAndroid.to_sql("tableAndroid", conn, if_exists="append", index=True)
conn.commit()


# Define the logic to update 'tableCombined' based on 'tableIOS' and 'tableAndroid'
def update_combined_table():
    # Drop existing 'tableCombined' if it exists
    cursor.execute("DROP TABLE IF EXISTS tableCombined")

    # Create 'tableCombined'
    cursor.execute(
        """
        CREATE TABLE tableCombined (
            Date DATE,
            'App Name' TEXT,
            'Avg App Rating' REAL,
            'Total Reviews' INTEGER,
            'iOS App Rating' REAL,
            'iOS Total Reviews' INTEGER,
            'Android App Rating' REAL,
            'Android Total Reviews' INTEGER,
            'Timestamp' TEXT
        )
    """
    )

    # Merge data from 'tableIOS' and 'tableAndroid' and insert into 'tableCombined'
    cursor.execute(
        """
        INSERT INTO tableCombined (
            'Date',
            'App Name',
            'Avg App Rating',
            'Total Reviews',
            'iOS App Rating',
            'iOS Total Reviews',
            'Android App Rating',
            'Android Total Reviews',
            'Timestamp'
        )
        SELECT
            t1.'Date',
            t2.'App Name',
            ROUND((t1.'iOS App Rating' + t2.'Android App Rating') / 2,2) AS 'Avg App Rating',
            t1.'iOS Total Reviews' + t2.'Android Total Reviews' AS 'Total Reviews',
            ROUND(t1.'iOS App Rating', 2) AS 'iOS App Rating',
            t1.'iOS Total Reviews',
            ROUND(t2.'Android App Rating', 2) AS 'Android App Rating',
            t2.'Android Total Reviews',
            t1.'Timestamp'
        FROM
            tableIOS AS t1
        INNER JOIN
            tableAndroid AS t2
        ON
            t1.Mapping = t2.Mapping AND t1.Date = t2.Date
    """
    )

    # Commit the changes to the database
    conn.commit()


# Call the update_combined_table() function to update 'tableCombined'
update_combined_table()

conn.close()
