import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import re

def parse_relative_date(relative_date):
    """
    Parse the relative date (e.g., "3d", "2m", "14h") and return a datetime object.
    """
    now = datetime.now()
    
    # Match the relative date format (e.g., 3d, 2m, 14h)
    match = re.match(r"(\d+)([a-zA-Z]+)", relative_date)
    
    if match:
        value = int(match.group(1))
        unit = match.group(2)
        
        if unit == 'd':  # days
            return now - timedelta(days=value)
        elif unit == 'h':  # hours
            return now - timedelta(hours=value)
        elif unit == 'm':  # months (approx 30 days)
            return now - timedelta(days=value * 30)
    
    return now  # Fallback to current date if format is unknown

def convert_string_to_datetime(date_string):
    """
    Convert the date string from JSON back into a datetime object.
    """
    try:
        # If the date is already in a datetime string format, convert it
        return datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        # If not, assume it's a relative date format and parse it
        return parse_relative_date(date_string)

def main():
    # Initialize JSON file with an empty list if it doesn't exist
    file_path = "result.json"
    try:
        with open(file_path, "r") as file:
            existing_data = json.load(file)
            # Convert the date strings in the existing data back into datetime objects
            for entry in existing_data:
                entry["date"] = convert_string_to_datetime(entry["date"])
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = []

    # Initialize the web driver
    driver = webdriver.Chrome()
    page_num = 1

    for i in range(25):
        url = f"https://web3.career/remote+top-web3-jobs?page={page_num}"
        driver.get(url)
        time.sleep(2)

        current_url = driver.current_url
        parsed_url = urlparse(current_url)
        query_params = parse_qs(parsed_url.query)

        current_page_num = int(query_params.get("page", [1])[0])

        # If the page number exceeds the current page, stop the loop
        if page_num > current_page_num:
            break
        else:
            print(f"Scraping page {page_num}")
            page_num += 1

            # Get job cards and extract information
            cards = driver.find_elements(By.CSS_SELECTOR, ".table_row")
            job_data = []
            for card in cards:
                relative_date = card.find_element(By.CSS_SELECTOR, "[style*='display: inline-block'][style*='width: 522px'][style*='margin-top: -86px'][style*='text-align: end']").text
                title = card.find_element(By.CSS_SELECTOR, ".mb-auto").text
                job_url = card.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

                # Convert relative date to actual datetime object
                job_date = parse_relative_date(relative_date)

                # Append job data
                job_data.append({
                    "date": job_date,
                    "title": title,
                    "job_url": job_url
                })

            # Append the new job data to the existing data
            existing_data.extend(job_data)

            # Sort the existing data by date (descending order, most recent first)
            existing_data.sort(key=lambda x: x['date'], reverse=True)
            existing_data = [data for data in existing_data if data["job_url"] != "https://web3.career/metana"]

            # Write the updated and sorted data back to the file
            with open(file_path, "w") as file:
                json.dump(existing_data, file, indent=4, default=str)

    driver.quit()

if __name__ == "__main__":
    main()
