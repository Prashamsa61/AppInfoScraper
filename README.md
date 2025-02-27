# 📱 Play Store Scraper  

## 📌 Project Overview  
**Play Store Scraper** is a web scraping tool designed to extract app details from the **Google Play Store**. It utilizes **Scrapy** and **Selenium** to navigate the Play Store, collect app details, and store the data for further use.  

## 🚀 Features
- ✅ Scrapes app details such as name, category, rating, reviews, and more.  
- ✅ Uses **Scrapy** for efficient data extraction.  
- ✅ Handles JavaScript-rendered content using **Selenium**.  
- ✅ Saves extracted data in an SQLite **database**.

## 📦 Package Manager  
This project uses **Poetry** as the package manager for dependency management. Poetry simplifies package installation, dependency resolution, and virtual environment management.

## 🛠️ Packages Used  
The following dependencies are used in this project:  

| Package   | Version Range  | Purpose |
|-----------|---------------|---------|
| `scrapy`  | >=2.12.0,<3.0.0 | A web scraping framework to extract data efficiently from the Play Store. |
| `selenium` | >=4.29.0,<5.0.0 | Used to interact with dynamic web content on the Play Store. |

## 🔧 Environment Setup  

### 1️⃣ Install Poetry  
If you haven't installed Poetry yet, use the following command:  

#### 📌 For Mac & Linux:  
```sh
curl -sSL https://install.python-poetry.org | python3 -
```

#### 📌 For Windows:  
Run the following command in **PowerShell** (as Administrator):  
```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```
For detailed installation steps, refer to the official [Poetry Installation Guide](https://python-poetry.org/docs/#installation).

### 2️⃣ Clone the Repository  
```sh
git clone https://github.com/your-username/playstore-scraper.git
cd playstore-scraper
```

### 3️⃣ Install Dependencies  
Once inside the project directory, install the required dependencies using Poetry:  
```sh
poetry install
```
This will set up a virtual environment and install all dependencies specified in `pyproject.toml`.

### 4️⃣ Activate the Virtual Environment  
Poetry automatically creates a virtual environment. To activate it, run:  
```sh
poetry env activate
```

### 5️⃣ Run the Scraper  
Execute the Scrapy spider to start extracting data:  
```sh
poetry run scrapy crawl scrapy_name
```

## 📁 Output Format

The scraped data is stored in the following formats:

1. **SQLite Database**  
   The data is saved in an SQLite database file named **`PlayStore_data.db`**.

2. **Tables in the Database**  
   The database contains two tables:
   - **`apps` table**: Contains information about the apps, including app name, category, rating, and other details.
   - **`reviews` table**: Contains reviews for each app, including review text, rating, and other relevant review information.

  
