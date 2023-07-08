from bs4 import BeautifulSoup
import requests
import json
from appURLs import appURLs

androidImages = []

androidURLs = [appURLs[apps]['android'] for apps in appURLs]
for url in androidURLs:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    script = parse.find(type="application/ld+json").text.strip()
    data = json.loads(script)
    appIconURL = data["image"]
    icon = result.content
    androidImages.append(icon)

iosImages = []

iosURLS = [appURLs[apps]['ios'] for apps in appURLs]

for url in iosURLS:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    script = parse.find(type="application/ld+json").text.strip()
    dataJSON = json.loads(script)
    appIconURL = data["image"]
    icon = result.content
    iosImages.append(icon)