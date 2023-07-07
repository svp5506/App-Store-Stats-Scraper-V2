from bs4 import BeautifulSoup
import requests
import json
from datetime import date, datetime
import pandas as pd
import sqlite3
from appURL import appURLs

# Timestamp and Date
timestamp = datetime.now()
dateFormatted = "{:%Y-%m-%d}".format(timestamp)

# Retrieve list of Android URLs
androidURLs = [appURLs[apps]['android'] for apps in appURLs]

data = []

# Loop through all Android URLs
for url in androidURLs:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    script = parse.find(type="application/ld+json").text.strip()
    dataJSON = json.loads(script)
    # App Name
    appName = dataJSON["name"]
    # Star Rating
    aggregateRating = dataJSON.get("aggregateRating")
    if aggregateRating is not None:
        starRatingDetail = aggregateRating.get("ratingValue")
        starRatingOfficial = round(float(aggregateRating.get("ratingValue")), 1)
    else:
        starRatingDetail = "Not Available"
        starRatingOfficial = "Not Available"
    # Total Reviews
    if aggregateRating is not None:
        totalReviews = aggregateRating.get("ratingCount")
    else:
        totalReviews = "Not Available"
    # Phone Rating Counts
    phoneRatings = parse.find_all("div", class_="JzwBgb")
    star1Count = star2Count = star3Count = star4Count = star5Count = None
    for rating in phoneRatings:
        phoneStarRating = rating.find(class_="Qjdn7d").get_text()
        reviews_label = rating["aria-label"]
        reviews_count = reviews_label.split(' ')[0].replace(',', '')
        
        if phoneStarRating == '1':
            star1Count = reviews_count
        elif phoneStarRating == '2':
            star2Count = reviews_count
        elif phoneStarRating == '3':
            star3Count = reviews_count
        elif phoneStarRating == '4':
            star4Count = reviews_count
        elif phoneStarRating == '5':
            star5Count = reviews_count
    
    # Append scraped data for each app
    data.append({
        'Date': dateFormatted,
        'App Name': appName,
        'App Rating': starRatingOfficial,
        'Total Reviews': totalReviews,
        'Detailed App Rating': starRatingDetail,
        '1 Star Reviews (Phone)': star1Count,
        '2 Star Reviews (Phone)': star2Count,
        '3 Star Reviews (Phone)': star3Count,
        '4 Star Reviews (Phone)': star4Count,
        '5 Star Reviews (Phone)': star5Count,
        'Timestamp': timestamp
    })

# Convert to Dataframe
dataAndroid = pd.DataFrame(data)
print(dataAndroid['Total Reviews'])

data = []

print(data)