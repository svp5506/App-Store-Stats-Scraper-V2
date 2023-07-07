from bs4 import BeautifulSoup
import requests
import json
from appURL import appURLs

images = []

androidURLs = [appURLs[apps]['android'] for apps in appURLs]
for url in androidURLs:
    result = requests.get(url)
    parse = BeautifulSoup(result.content, "lxml")
    # Retrieve and parse JSON
    script = parse.find(type="application/ld+json").text.strip()
    data = json.loads(script)
    appIconURL = data["image"]
    icon = result.content
    images.append(icon)

