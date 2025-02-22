import sqlite3
import csv
import os


class DatabaseManager:
    def __init__(self, db_name="playstore_data.db", csv_file="playstore_data.csv"):
        """Initialize SQLite connection and CSV setup."""
        self.db_name = db_name
        self.csv_file = csv_file

        # Initialize SQLite database
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

        # Initialize CSV file
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(
                    [
                        "category",
                        "title",
                        "rating",
                        "version",
                        "review_count",
                        "downloads",
                        "age_suitability",
                        "updated_on",
                        "ads",
                    ]
                )

    def create_table(self):
        """Create SQLite table if not exists."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS apps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                rating TEXT,
                version TEXT,
                review_count TEXT,
                downloads TEXT,
                age_suitability TEXT,
                updated_on TEXT,
                ads TEXT
            )
            """
        )
        self.conn.commit()

    def insert_data(self, data):
        """Insert data into SQLite and CSV."""
        # Insert into SQLite
        self.cursor.execute(
            """
            INSERT INTO apps (category, title, rating, version, review_count, downloads, age_suitability, updated_on, ads)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["category"],
                data["title"],
                data["rating"],
                data["version"],
                data["review_count"],
                data["downloads"],
                data["age_suitability"],
                data["updated_on"],
                data["ads"],
            ),
        )
        self.conn.commit()

        # Insert into CSV
        with open(self.csv_file, mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(data.values())

    def close(self):
        """Close SQLite connection."""
        self.conn.close()
