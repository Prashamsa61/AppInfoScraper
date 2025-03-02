import csv
import os

categories = {
    "ART_AND_DESIGN": "https://play.google.com/store/apps/category/ART_AND_DESIGN?hl=en",
    "AUTO_AND_VEHICLES": "https://play.google.com/store/apps/category/AUTO_AND_VEHICLES?hl=en",
    "BOOKS_AND_REFERENCE": "https://play.google.com/store/apps/category/BOOKS_AND_REFERENCE?hl=en",
    "BUSINESS": "https://play.google.com/store/apps/category/BUSINESS",
    "COMICS": "https://play.google.com/store/apps/category/COMICS",
    "COMMUNICATION": "https://play.google.com/store/apps/category/COMMUNICATION",
    "DATING": "https://play.google.com/store/apps/category/DATING",
    "EDUCATION": "https://play.google.com/store/apps/category/EDUCATION",
    "ENTERTAINMENT": "https://play.google.com/store/apps/category/ENTERTAINMENT",
    "EVENTS": "https://play.google.com/store/apps/category/EVENTS",
    "FINANCE": "https://play.google.com/store/apps/category/FINANCE",
    "FOOD_AND_DRINK": "https://play.google.com/store/apps/category/FOOD_AND_DRINK?hl=en",
    "HEALTH_AND_FITNESS": "https://play.google.com/store/apps/category/HEALTH_AND_FITNESS?hl=en",
    "HOUSE_AND_HOME": "https://play.google.com/store/apps/category/HOUSE_AND_HOME?hl=en",
    "LIBRARIES_AND_DEMO": "https://play.google.com/store/apps/category/LIBRARIES_AND_DEMO?hl=en",
    "LIFESTYLE": "https://play.google.com/store/apps/category/LIFESTYLE",
    "MAPS_AND_NAVIGATION": "https://play.google.com/store/apps/category/MAPS_AND_NAVIGATION?hl=en",
    "MUSIC_AND_AUDIO": "https://play.google.com/store/apps/category/MUSIC_AND_AUDIO?hl=en",
    "NEWS_AND_MAGAZINES": "https://play.google.com/store/apps/category/NEWS_AND_MAGAZINES?hl=en",
    "PARENTING": "https://play.google.com/store/apps/category/PARENTING",
    "PERSONALIZATION": "https://play.google.com/store/apps/category/PERSONALIZATION",
    "PHOTOGRAPHY": "https://play.google.com/store/apps/category/PHOTOGRAPHY",
    "PRODUCTIVITY": "https://play.google.com/store/apps/category/PRODUCTIVITY",
    "SHOPPING": "https://play.google.com/store/apps/category/SHOPPING",
    "SOCIAL": "https://play.google.com/store/apps/category/SOCIAL",
    "SPORTS": "https://play.google.com/store/apps/category/SPORTS",
    "TOOLS": "https://play.google.com/store/apps/category/TOOLS",
    "TRAVEL_AND_LOCAL": "https://play.google.com/store/apps/category/TRAVEL_AND_LOCAL?hl=en",
    "VIDEO_PLAYERS_AND_EDITORS": "https://play.google.com/store/apps/category/VIDEO_PLAYERS?hl=en",
    "WEATHER": "https://play.google.com/store/apps/category/WEATHER",
    "ACTION": "https://play.google.com/store/apps/category/GAME_ACTION?h1=en",
    "ADVENTURE": "https://play.google.com/store/apps/category/GAME_ADVENTURE",
    "ARCADE": "https://play.google.com/store/apps/category/GAME_ARCADE?h1=en",
    "BOARD": "https://play.google.com/store/apps/category/GAME_BOARD?h1=en",
    "CARD": "https://play.google.com/store/apps/category/GAME_CARD?h1=en",
    "CASINO": "https://play.google.com/store/apps/category/GAME_CASINO?h1=en",
    "CASUAL": "https://play.google.com/store/apps/category/GAME_CASUAL",
    "EDUCATIONAL": "https://play.google.com/store/apps/category/EDUCATION?hl=en",
    "PUZZLE": "https://play.google.com/store/apps/category/GAME_PUZZLE?h1=en",
    "RACING": "https://play.google.com/store/apps/category/GAME_RACING",
    "ROLE_PLAYING": "https://play.google.com/store/apps/category/GAME_ROLE_PLAYING?hl=en",
    "SIMULATION": "https://play.google.com/store/apps/category/GAME_SIMULATION?hl=en",
    "SPORTS_GAMES": "https://play.google.com/store/apps/category/GAME_SPORTS?hl=en",
    "STRATEGY": "https://play.google.com/store/apps/category/GAME_STRATEGY?hl=en",
    "TRIVIA": "https://play.google.com/store/apps/category/GAME_TRIVIA?hl=en",
    "WORD": "https://play.google.com/store/apps/category/GAME_WORD?hl=en",
}

# File path
csv_file_path = os.path.join("output", "categories.csv")

# Write data to CSV file
with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Category", "URL"])
    for category, url in categories.items():
        writer.writerow([category, url])

print("CSV file has been created.")
