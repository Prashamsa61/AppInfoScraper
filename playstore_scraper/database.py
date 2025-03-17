import sqlite3


class DatabaseManager:
    def __init__(self, db_name="playstore_data.db"):
        """Initialize SQLite connection and CSV setup."""
        self.db_name = db_name

        # Initialize SQLite database
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

        # Initialize tables
        self.create_apps_table()
        self.create_reviews_table()

    def create_apps_table(self):
        """Create the apps table in SQLite if not exists."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS apps (
                AppID INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                title TEXT,
                rating TEXT,
                version TEXT,
                review_count TEXT,
                downloads TEXT,
                age_suitability TEXT,
                updated_on TEXT,
                ads TEXT,
                requires_android TEXT,
                In_app_purchases TEXT,
                price TEXT,
                ranking_category TEXT
            )

            """
        )
        self.conn.commit()

    def create_reviews_table(self):
        """Create the reviews table in SQLite if not exists."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS reviews(
                Review_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                AppID INTEGER,
                Reviewer_Name TEXT,
                Review TEXT,
                Review_Date TEXT,
                Rating INTEGER,
                FOREIGN KEY (AppID) REFERENCES apps(AppID) ON DELETE CASCADE
            )
            """
        )
        self.conn.commit()

    def insert_app_data(self, data):
        """Insert app data into SQLite"""

        # Skip insertion if no title
        if not data.get("title"):
            return

        self.cursor.execute(
            """
            INSERT OR IGNORE INTO apps (category, title, rating, version, review_count, downloads, age_suitability, updated_on, ads,requires_android, In_app_purchases,price,ranking_category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)
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
                data["requires_android"],
                data["In_app_purchases"],
                data["price"],
                data["ranking_category"],
            ),
        )
        self.conn.commit()

    def read_database(self):
        """Reads the database and returns a list of all app IDs and titles."""
        try:
            conn = sqlite3.connect("../playstore_data.db")
            cursor = conn.cursor()

            # Execute the query to fetch all app IDs and titles
            cursor.execute("SELECT AppID, title FROM apps")
            results = cursor.fetchall()

            # Store the results in a list of tuples (AppID, title)
            app_data = [{"AppID": row[0], "title": row[1]} for row in results]

            return app_data
        except Exception as e:
            print(f"Error reading database: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def insert_review_data(self, app_id, reviews):
        """Insert review data linked to an app."""
        # Loop through each review and insert it into the reviews table
        for review in reviews:
            reviewer_name = review["reviewer_name"]
            review_text = review["review_text"]
            review_date = review["review_date"]
            rating = review["review_rating"]

            # Insert the review into the reviews table, linking with AppID
            self.cursor.execute(
                """
                INSERT INTO reviews (AppID, Reviewer_Name, Review, Review_Date, Rating)
                VALUES (?, ?, ?, ?, ?)
                """,
                (app_id, reviewer_name, review_text, review_date, rating),
            )
            self.conn.commit()

    def close(self):
        """Close SQLite connection."""
        self.conn.close()
