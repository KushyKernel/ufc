import requests      # For sending HTTP requests to websites
import time          # For implementing delays between requests
import random        # For generating random delays to avoid detection
import json          # For encoding and decoding JSON data
from bs4 import BeautifulSoup  # For parsing HTML content from web pages
from googlesearch import search  # For performing Google searches

# ================================
# UFC Data Scraping Section
# ================================

# Define the base URL for the UFC athlete listing page
base_url = "https://www.ufc.com/athletes/all"

# Define HTTP headers to simulate a real browser request
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/114.0.0.0 Safari/537.36"
    )
}

page = 1  # Start scraping from page 1
all_data = []  # List to store tuples of (athlete_name, full_profile_link)
reported_hundreds = 0  # Tracker for logging progress every ~110 entries

# Loop through the pages until no more athlete cards are found
while True:
    # Define query parameters for the current page
    params = {
        "gender": "All",  # Retrieve athletes of all genders
        "search": "",     # No search term to filter the list
        "page": page      # Current page number
    }
    
    # Send a GET request to the UFC athlete page with the given parameters and headers
    response = requests.get(base_url, headers=headers, params=params)
    
    # If the request fails (status code is not 200), print an error and exit the loop
    if response.status_code != 200:
        print("Error: Status code", response.status_code)
        break

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find all the athlete card elements on the page using their CSS class
    cards = soup.find_all("div", class_="c-listing-athlete-flipcard")
    
    # If no athlete cards are found, assume there are no more pages and exit the loop
    if not cards:
        print("No athlete cards found on page", page, "- exiting loop.")
        break

    # Process each athlete card on the page
    for card in cards:
        # Look for the <a> tag that includes the class "e-button--black" (which holds the profile link)
        link_tag = card.find("a", class_=lambda x: x and "e-button--black" in x)
        if link_tag:
            # Find the nested <span> tag that confirms the link is for an "Athlete Profile"
            text_tag = link_tag.find("span", class_="e-button__text")
            if text_tag and "Athlete Profile" in text_tag.get_text(strip=True):
                # Extract the URL (href) from the link tag
                href = link_tag.get("href")
                # If the URL is relative (starts with "/"), build the full URL
                if href.startswith("/"):
                    full_link = "https://www.ufc.com" + href
                else:
                    full_link = href
                # Extract the athlete's name from the card
                name_tag = card.find("span", class_="c-listing-athlete__name")
                athlete_name = name_tag.get_text(strip=True) if name_tag else "Unknown"
                # Append the athlete's name and profile URL as a tuple to the list
                all_data.append((athlete_name, full_link))
    
    # Log progress every time the total count increases by approximately 110 entries
    if len(all_data) // 110 > reported_hundreds:
        reported_hundreds = len(all_data) // 110
        print(f"Total athlete profile links so far: {len(all_data)}")
    
    # Move to the next page
    page += 1

# After scraping, print the total number of athlete profiles found
print("Total athlete profile links found:", len(all_data))

# Convert the list of tuples into a list of dictionaries for easier JSON conversion and processing
result_ufc = [{"name": name, "ufc_url": link} for name, link in all_data]
# Convert the UFC fighter data to a JSON-formatted string (optional, e.g., for saving to a file)
ufc_fighters = json.dumps(result_ufc, indent=2)

# ================================
# Sherdog Data Scraping Section
# ================================

# Convert the UFC fighter JSON string back into a Python list (simulating loading previously saved data)
ufc_data = json.loads(ufc_fighters)

# Extract just the fighter names from the UFC data to use in Sherdog search queries
fighter_names = [fighter["name"] for fighter in ufc_data]

result_sd = []  # List to store search results for Sherdog profiles
max_retries = 5  # Maximum number of retry attempts for a search query

# Iterate over each fighter name from the UFC dataset
for fighter in fighter_names:
    # Formulate the search query string combining fighter name with "Sherdog"
    query = f"{fighter} Sherdog"
    retry_count = 0  # Initialize a counter for the number of retries
    fighter_data = {"name": fighter, "url": None}  # Dictionary to hold the search result
    
    # Attempt the search with a retry mechanism in case of errors
    while retry_count < max_retries:
        try:
            # Perform the Google search; only the top result is needed
            search_results = list(search(query, num_results=1))
            if search_results:
                # If a result is found, store the URL in the dictionary
                fighter_data["url"] = search_results[0]
            break  # Exit the retry loop if successful
        except Exception as e:
            # If an error occurs, print the error message
            print(f"Error retrieving results for {fighter}: {e}")
            retry_count += 1
            # Calculate a delay using exponential backoff with randomness before retrying
            backoff_delay = random.uniform(1, 5) * (2 ** retry_count)
            print(f"Retrying in {backoff_delay:.2f} seconds... (attempt {retry_count}/{max_retries})")
            time.sleep(backoff_delay)
    
    # Append the fighter's Sherdog search result (name and URL) to the result list
    result_sd.append(fighter_data)
    # Add a random delay between successive search queries to reduce the chance of being blocked
    time.sleep(random.uniform(1, 5))

# Print the Sherdog search results in a formatted JSON structure for debugging or review
print("Sherdog Search Results:")
print(json.dumps(result_sd, indent=2))

# Optionally, create a list of dictionaries with a descriptive key ("sherdog_url") for each fighter
result_sherdog = [{"name": fighter["name"], "sherdog_url": fighter["url"]} for fighter in result_sd]
sherdog_fighters = json.dumps(result_sherdog, indent=2)

# ================================
# Merging UFC and Sherdog Data Section
# ================================

# Create a lookup dictionary for Sherdog data keyed by fighter name for efficient access
sherdog_dict = {fighter['name']: fighter for fighter in result_sd}

# Perform a left join based on UFC data:
# For each fighter in the UFC dataset, attempt to add corresponding Sherdog data if available.
data_source = []
for fighter in ufc_data:
    name = fighter["name"]  # Get fighter name from UFC data
    # Retrieve the Sherdog data for this fighter (if it exists) using the lookup dictionary
    sher_data = sherdog_dict.get(name)
    # Create a merged record containing the fighter's name, UFC URL, and Sherdog URL (if found)
    merged_fighter = {
        "name": name,
        "ufc_url": fighter["ufc_url"],
        "sherdog_url": sher_data.get("url") if sher_data else None
    }
    # Append the merged record to the final dataset
    data_source.append(merged_fighter)

