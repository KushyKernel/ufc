import requests         # For sending HTTP requests
import time             # For delays between requests
import random           # For generating random delays
import json             # For encoding/decoding JSON data
from bs4 import BeautifulSoup  # For parsing HTML content
from googlesearch import search  # For performing Google searches

def scrape_ufc_data():
    """
    Scrapes the UFC website to collect fighter names and their profile URLs.
    Returns a list of dictionaries with keys: 'name' and 'ufc_url'.
    """
    base_url = "https://www.ufc.com/athletes/all"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
    }
    page = 1
    all_data = []           # To store tuples: (athlete_name, full_profile_link)
    reported_hundreds = 0   # To log progress after approximately every 110 entries

    while True:
        params = {"gender": "All", "search": "", "page": page}
        response = requests.get(base_url, headers=headers, params=params)
        if response.status_code != 200:
            print("Error: Status code", response.status_code)
            break

        soup = BeautifulSoup(response.content, "html.parser")
        cards = soup.find_all("div", class_="c-listing-athlete-flipcard")
        if not cards:
            print(f"No athlete cards found on page {page} - exiting loop.")
            break

        for card in cards:
            # Find the link tag with the 'e-button--black' class
            link_tag = card.find("a", class_=lambda x: x and "e-button--black" in x)
            if link_tag:
                # Confirm the link is for an Athlete Profile
                text_tag = link_tag.find("span", class_="e-button__text")
                if text_tag and "Athlete Profile" in text_tag.get_text(strip=True):
                    href = link_tag.get("href")
                    # If the link is relative, prepend the UFC domain
                    full_link = "https://www.ufc.com" + href if href.startswith("/") else href
                    # Extract fighter name
                    name_tag = card.find("span", class_="c-listing-athlete__name")
                    athlete_name = name_tag.get_text(strip=True) if name_tag else "Unknown"
                    all_data.append((athlete_name, full_link))
        
        if len(all_data) // 110 > reported_hundreds:
            reported_hundreds = len(all_data) // 110
            print(f"Total athlete profile links so far: {len(all_data)}")
        
        page += 1

    print("Total athlete profile links found:", len(all_data))
    # Convert to list of dictionaries for easy processing
    return [{"name": name, "ufc_url": link} for name, link in all_data]

def search_sherdog_profiles(ufc_data):
    """
    Uses Google search to find Sherdog profile URLs for each fighter in ufc_data.
    Returns a list of dictionaries with each fighter's name and the Sherdog URL (if found).
    """
    fighter_names = [fighter["name"] for fighter in ufc_data]
    result_sd = []  # To store Sherdog search results
    max_retries = 5

    for fighter in fighter_names:
        query = f"{fighter} Sherdog"
        retry_count = 0
        fighter_data = {"name": fighter, "url": None}
        
        while retry_count < max_retries:
            try:
                # Get the top result for the query
                search_results = list(search(query, num_results=1))
                if search_results:
                    fighter_data["url"] = search_results[0]
                break  # Exit loop if successful
            except Exception as e:
                print(f"Error retrieving results for {fighter}: {e}")
                retry_count += 1
                backoff_delay = random.uniform(1, 5) * (2 ** retry_count)
                print(f"Retrying in {backoff_delay:.2f} seconds... (attempt {retry_count}/{max_retries})")
                time.sleep(backoff_delay)
        
        result_sd.append(fighter_data)
        # Pause between queries to avoid being blocked
        time.sleep(random.uniform(1, 5))

    print("Sherdog Search Results:")
    print(json.dumps(result_sd, indent=2))
    return result_sd

def merge_data(ufc_data, sherdog_results):
    """
    Merges UFC data with Sherdog results based on fighter names.
    Returns a list of dictionaries with keys: 'name', 'ufc_url', and 'sherdog_url'.
    """
    # Create a lookup dictionary for Sherdog data
    sherdog_dict = {fighter['name']: fighter for fighter in sherdog_results}
    merged_data = []
    for fighter in ufc_data:
        name = fighter["name"]
        sher_data = sherdog_dict.get(name)
        merged_fighter = {
            "name": name,
            "ufc_url": fighter["ufc_url"],
            "sherdog_url": sher_data.get("url") if sher_data else None
        }
        merged_data.append(merged_fighter)
    return merged_data

def main():
    # Step 1: Scrape UFC website to get fighter names and URLs
    ufc_data = scrape_ufc_data()
    
    # Step 2: Use Google search to get Sherdog profile URLs for each fighter
    sherdog_results = search_sherdog_profiles(ufc_data)
    
    # Step 3: Merge the UFC data with Sherdog search results
    merged_data = merge_data(ufc_data, sherdog_results)
    
    # Step 4: Save the merged data to a JSON file
    output_file = "merged_data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, indent=2)
    print(f"Merged data saved to {output_file}")

if __name__ == '__main__':
    main()
