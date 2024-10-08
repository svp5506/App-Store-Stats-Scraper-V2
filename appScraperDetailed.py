from bs4 import BeautifulSoup
import pytz
import requests
import json
from datetime import datetime
import pandas as pd
from appURLs import appURLs

# Timestamp and Date
mountain = pytz.timezone('US/Mountain')
timestamp = datetime.now(mountain)
dateFormatted = "{:%Y-%m-%d}".format(timestamp)

# Scrape Android Data
data = []
# Retrieve list of Android URLs
androidURLs = [appURLs[apps]["android"] for apps in appURLs]
# Create a reverse mapping from Android URLs to the corresponding app name
androidURLNameMapping = {appURLs[app]["android"]: app for app in appURLs}
# Loop through all Android URLs
for url in androidURLs:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # App Name
    appName = androidURLNameMapping.get(url)
    # Retrieve and parse JSON
    json_element = parse.find(type="application/ld+json")
    if json_element is not None:
        script = json_element.text.strip()
        dataJSON = json.loads(script)
        # Star Rating
        aggregateRating = dataJSON.get("aggregateRating")
        if aggregateRating is not None:
            starRatingDetail = aggregateRating.get("ratingValue")
            starRatingOfficial = float(aggregateRating.get("ratingValue"))
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
        data.append(
            {
                "Date": dateFormatted,
                "App Name": appName,
                "Android App Rating": "Not Available",
                "Android Total Reviews": "Not Available",
                "Android Detailed App Rating": "Not Available",
                "1 Star Reviews (Phone)": "Not Available",
                "2 Star Reviews (Phone)": "Not Available",
                "3 Star Reviews (Phone)": "Not Available",
                "4 Star Reviews (Phone)": "Not Available",
                "5 Star Reviews (Phone)": "Not Available",
                "Android App Category": "Not Available",
                "Timestamp": timestamp,
            }
        )
        continue

# Convert to Dataframe
dataAndroid = pd.DataFrame(data)

# Scrape iOS Data
data = []
# Retrieve list of iOS URLs
iosURLS = [appURLs[apps]["ios"] for apps in appURLs]
# Create a reverse mapping from iOS URLs to the corresponding app name
iosURLNameMapping = {appURLs[app]["ios"]: app for app in appURLs}
# Loop through all iOS URLs
for url in iosURLS:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # App Name
    appName = iosURLNameMapping.get(url)
    # Retrieve and parse JSON
    json_element = parse.find(type="application/ld+json")
    if json_element is not None:
        script = json_element.text.strip()
        dataJSON = json.loads(script)
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
        data.append(
            {
                "Date": dateFormatted,
                "App Name": "Not Available",
                "iOS App Rating": "Not Available",
                "iOS Total Reviews": "Not Available",
                "iOS App Rank": "Not Available",
                "iOS App Category": "Not Available",
                "Timestamp": timestamp,
            }
        )
        continue

# Convert to Dataframe
dataIos = pd.DataFrame(data)

dataAndroidTemp = dataAndroid.copy()
dataAndroidTemp["App Name"] = dataIos["App Name"]

# Merge the Android and iOS DataFrames based on fuzzy matching of app names (using inner join)
combinedData = pd.merge(dataIos, dataAndroidTemp, on="App Name", how="inner")

# Drop unnecessary columns
combinedData = combinedData.drop(
    [
        "Timestamp_x",
        "Date_y",
        "Android Detailed App Rating",
        "1 Star Reviews (Phone)",
        "2 Star Reviews (Phone)",
        "3 Star Reviews (Phone)",
        "4 Star Reviews (Phone)",
        "5 Star Reviews (Phone)",
        "Android App Category",
        "iOS App Category",
    ],
    axis=1,
)

# Rename the remaining columns
combinedData = combinedData.rename(
    columns={"Timestamp_y": "Timestamp", "Date_x": "Date"}
)

# Calculate the average of iOS and Android app ratings (same as before)
combinedData['Overall App Rating'] = pd.to_numeric(combinedData['iOS App Rating'], errors='coerce').add(pd.to_numeric(combinedData['Android App Rating'], errors='coerce')) / 2

# Convert the 'Android Total Reviews' and 'iOS Total Reviews' columns to numeric (integer) data type
combinedData['Android Total Reviews'] = pd.to_numeric(combinedData['Android Total Reviews'], errors='coerce').fillna(0).astype(int)
combinedData['iOS Total Reviews'] = pd.to_numeric(combinedData['iOS Total Reviews'], errors='coerce').fillna(0).astype(int)

# Now, you can perform the addition safely
combinedData['Combined Total Reviews'] = combinedData['Android Total Reviews'] + combinedData['iOS Total Reviews']

# Export the combined DataFrame to a CSV file
combinedData.to_csv("dataDetailed.csv", index=False)
