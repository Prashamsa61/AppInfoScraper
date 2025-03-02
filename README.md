# 📱 Play Store Scraper  

## 📌 Project Overview  
**Play Store Scraper** is a web scraping tool designed to extract app details from the **Google Play Store**. It utilizes **Scrapy** and **Selenium** to navigate the Play Store, collect app details, and store the data for further use.  

## 🚀 Features  
- ✅ Scrapes app details such as name, category, rating, reviews, and more.  
- ✅ Uses **Scrapy** for efficient data extraction.  
- ✅ Handles JavaScript-rendered content using **Selenium**.  
- ✅ Saves extracted data in an SQLite **database** for easy querying.  

## 📦 Package Manager  
This project uses **Poetry** for dependency management. Poetry simplifies package installation, dependency resolution, and virtual environment management.  

## 🛠️ Packages Used  
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

## 🔍 How the Scraper Works  

### ✅ Scrapy + Selenium Integration  
This scraper efficiently combines **Scrapy** and **Selenium** to extract app details from the **Google Play Store**:  

- **Scrapy** handles:  
  - The overall crawling logic and URL processing.  
  - Initial page requests and parsing static HTML content.  
  - Managing request scheduling and queuing.  

- **Selenium** is used within Scrapy’s `parse_app` method to:  
  - Render JavaScript-powered pages.  
  - Expand hidden sections (e.g., "Read More" in app descriptions).  
  - Extract dynamically loaded data such as versions and reviews.  


### ✅ Scraping Process  

1️⃣ **Starting the Scraper**  
   - The scraper requests category pages from the **Google Play Store**.  
   - It extracts links to individual apps for further scraping.  

2️⃣ **Navigating to App Pages**  
   - Each app page is loaded using **Selenium** to handle JavaScript execution.  
   - The scraper clicks the "arrow" button when necessary to reveal full descriptions.  

3️⃣ **Extracting Data**  
   The following details are collected for each app:  
   - **App Name**  
   - **Category**  
   - **Rating**  
   - **Version**  
   - **Number of Reviews**  
   - **Downloads Count**  
   - **Age Suitability**  
   - **Last Updated Date**  
   - **Presence of Ads**
   - **Price**
   - **Reviews**

4️⃣ **Storing in SQLite Database**  
   - Extracted app details are saved in the `apps` table.  
   - If reviews are collected, they are stored in the `reviews` table and linked to the corresponding app.  

## 📁 Output Format  

The scraped data is stored in an **SQLite database** named **`PlayStore_data.db`**.  

### **Tables in the Database**  
- **`apps` table**: Contains information about the apps, including app name, category, rating, and other details.  
- **`reviews` table**: Stores user reviews, including review text, rating, and other relevant review information.  

## ✅ Error Handling & Optimization  

### 🛠 Handling Missing Elements  
- If an expected field is unavailable, a warning is logged instead of stopping execution.  

### 🛠 Throttling & CAPTCHA Avoidance  
To prevent **CAPTCHA blocks** and ensure smooth scraping, the scraper implements the following strategies:  
- Introduces **delays (`time.sleep(2)`)** between requests.  
- Runs **Selenium in headless mode** for efficiency.  
- Uses **WebDriverWait** instead of fixed delays to optimize page load time.  

## 🔮 Conclusion  
This **Google Play Store Scraper** successfully integrates Scrapy and Selenium to efficiently extract and store app data.  

✅ **Scrapy** manages crawling and request scheduling.  
✅ **Selenium** handles JavaScript-loaded content.  
✅ **Data** is structured and stored in an SQLite database for easy querying.  

