from bs4 import BeautifulSoup
import requests
import json
from datetime import datetime
import pandas as pd
from appURLs import appURLs

# Timestamp and Date
timestamp = datetime.now()
dateFormatted = "{:%Y-%m-%d}".format(timestamp)

# Scrape Android Data
data = []
# Retrieve list of Android URLs
androidURLs = [appURLs[apps]["android"] for apps in appURLs]
# Loop through all Android URLs
for url in androidURLs:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    json_element = parse.find(type="application/ld+json")
    if json_element is not None:
        script = json_element.text.strip()
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
            reviews_count = reviews_label.split(" ")[0].replace(",", "")

            if phoneStarRating == "1":
                star1Count = reviews_count
            elif phoneStarRating == "2":
                star2Count = reviews_count
            elif phoneStarRating == "3":
                star3Count = reviews_count
            elif phoneStarRating == "4":
                star4Count = reviews_count
            elif phoneStarRating == "5":
                star5Count = reviews_count
        # App Category
        appCategory = dataJSON.get("applicationCategory", "Not Available")

        # Append scraped data for each app
        data.append(
            {
                "Date": dateFormatted,
                "App Name": appName,
                "Android App Rating": starRatingOfficial,
                "Android Total Reviews": totalReviews,
                "Android Detailed App Rating": starRatingDetail,
                "1 Star Reviews (Phone)": star1Count,
                "2 Star Reviews (Phone)": star2Count,
                "3 Star Reviews (Phone)": star3Count,
                "4 Star Reviews (Phone)": star4Count,
                "5 Star Reviews (Phone)": star5Count,
                "Android App Category": appCategory,
                "Timestamp": timestamp,
            }
        )
    else:
        # Handle the case when the JSON element is not found
        # You may want to log a message or take appropriate action here
        continue

# Convert to Dataframe for Android
dataAndroid = pd.DataFrame(data)

# Export Android DataFrame to CSV
dataAndroid.to_csv("android_data.csv", index=False)

# Scrape iOS Data
data = []
# Retrieve list of iOS URLs
iosURLS = [appURLs[apps]["ios"] for apps in appURLs]
# Loop through all iOS URLs
for url in iosURLS:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    json_element = parse.find(type="application/ld+json")
    if json_element is not None:
        script = json_element.text.strip()
        dataJSON = json.loads(script)
        # App Name
        appName = dataJSON["name"]
        # Star Rating
        aggregateRating = dataJSON.get("aggregateRating")
        if aggregateRating is not None:
            starRatingOfficial = aggregateRating.get("ratingValue")
        else:
            starRatingOfficial = "Not Available"
        # Total Reviews
        if aggregateRating is not None:
            totalReviews = aggregateRating.get("reviewCount")
        else:
            totalReviews = "Not Available"
        # App Store Category Rank
        rank_element = parse.find("a", {"class": "inline-list__item"})
        rank = None
        if rank_element is not None:
            rank_text = rank_element.text.strip().split()[0]
            rank = int(rank_text.replace(",", "").replace("#", ""))
        # App Category
        appCategory = dataJSON.get("applicationCategory", "Not Available")
        # Append scraped data for each app
        data.append(
            {
                "Date": dateFormatted,
                "App Name": appName,
                "iOS App Rating": starRatingOfficial,
                "iOS Total Reviews": totalReviews,
                "iOS App Rank": rank,
                "iOS App Category": appCategory,
                "Timestamp": timestamp,
            }
        )
    else:
        # Handle the case when the JSON element is not found
        # You may want to log a message or take appropriate action here
        continue

# Convert to Dataframe for iOS
dataIos = pd.DataFrame(data)

# Export iOS DataFrame to CSV
dataIos.to_csv("ios_data.csv", index=False)
