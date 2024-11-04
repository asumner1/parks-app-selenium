from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import pandas as pd
from datetime import datetime


# Add user input before any other code
while True:
    skip_selenium = input("Skip Selenium and only process existing CSV? (Y/N): ").upper()
    if skip_selenium in ['Y', 'N']:
        break
    print("Please enter Y or N")

park_names = [
    "Acadia",
    "American Samoa",
    "Arches",
    "Badlands",
    "Big Bend",
    "Biscayne",
    "Black Canyon of the Gunnison",
    "Bryce Canyon",
    "Canyonlands",
    "Capitol Reef",
    "Carlsbad Caverns",
    "Channel Islands",
    "Congaree",
    "Crater Lake",
    "Cuyahoga Valley",
    "Death Valley",
    "Denali",
    "Dry Tortugas",
    "Everglades",
    "Gates of the Arctic",
    "Gateway Arch",
    "Glacier",
    "Glacier Bay",
    "Grand Canyon",
    "Grand Teton",
    "Great Basin",
    "Great Sand Dunes",
    "Great Smoky Mountains",
    "Guadalupe Mountains",
    "Haleakalā",
    "Hawaiʻi Volcanoes",
    "Hot Springs",
    "Indiana Dunes",
    "Isle Royale",
    "Joshua Tree",
    "Katmai",
    "Kenai Fjords",
    "Kings Canyon",
    "Kobuk Valley",
    "Lake Clark",
    "Lassen Volcanic",
    "Mammoth Cave",
    "Mesa Verde",
    "Mount Rainier",
    "New River Gorge",
    "North Cascades",
    "Olympic",
    "Petrified Forest",
    "Pinnacles",
    "Redwood",
    "Rocky Mountain",
    "Saguaro",
    "Sequoia",
    "Shenandoah",
    "Theodore Roosevelt",
    "Virgin Islands",
    "Voyageurs",
    "White Sands",
    "Wind Cave",
    "Wrangell-St. Elias",
    "Yellowstone",
    "Yosemite",
    "Zion"
]

test_park_names = ["Grand Teton"]

park_region_words = [
    'peninsula',
    'island',
    'desert',
    'isle',
    'valley',
    'canyon',
    'mountain',
    'lake',
    'river',
    'forest',
    'cave',
    'spring',
    'bay',
    'arch',
    'dune',
    'gorge',
    'fjord',
    'volcano',
    'sand',
    'basin',
    'peak',
    'cliff',
    'ridge',
    'falls',
    'park',
    'trail',
    'meadow',
    'geyser',
    'reef',
    'marsh',
    'swamp',
    'prairie',
    'grassland',
    'tundra',
    'rainforest',
    'pond'
]
for i in range(len(park_region_words)):
    park_region_words.append(park_region_words[i] + 's')


def try_parsing_date_to_timestamp(text):
    for fmt in ('%Y-%m-%d', '%Y/%m/%d'):
        try:
            return datetime.strptime(text, fmt).timestamp()
        except ValueError:
            pass
    raise ValueError('no valid date format found')

# Wrap the Selenium portion in a condition
if skip_selenium != 'Y':
    try:
        driver = webdriver.Chrome()
        # Navigate to the NPS website
        driver.get("https://www.nps.gov/media/photo/collection.htm?pg=7323739&id=305fb7af-a71b-469b-941e-a98b439c882f&p=1&state=")
        time.sleep(5)

        park_map_links = []
        map_type = []

        for park_name in park_names:
            # Remove accent marks and apostrophes from park name
            park_name = park_name.replace("ʻ", "").replace("ā", "a")
            
            # Define edge case xpath additions
            edge_case_xpath = "[not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '3d '))]"
            if park_name == "Glacier":
                edge_case_xpath += "[not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'glacier bay'))]"
            elif park_name == "Arches":
                edge_case_xpath += "[not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'gateway arch'))]"

            def perform_search(driver, park_name):
                # Wait for page to load
                WebDriverWait(driver, 10).until(
                    lambda driver: driver.execute_script('return document.readyState') == 'complete'
                )
                
                # Wait for and find the specific search input field
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "allFields"))
                )
                # Scroll search input into view
                driver.execute_script("arguments[0].scrollIntoView(true);", search_input)
                time.sleep(1)
                search_input.clear()
                search_input.send_keys(f"Park Map - {park_name}")
                # Find and click the specific search button
                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-submit.btn-primary"))
                )
                # Scroll search button into view
                driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                time.sleep(1)
                search_button.click()

            try:
                perform_search(driver, park_name)
            except Exception as e:
                print(f"Error occurred, refreshing page and retrying: {str(e)}")
                driver.refresh()
                perform_search(driver, park_name)

            time.sleep(8)

            print(f"\n{park_name}:")
            print("-" * 50)
            current_map_type = "N/A"  # Initialize map type variable
            try:
                # Modified to find all park map elements
                xpath_query = f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'park map') or contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'park and area maps')]{edge_case_xpath}"
                map_elements = driver.find_elements(By.XPATH, xpath_query)
                
                if map_elements:
                    if len(map_elements) == 1:
                        # If only one element, use it directly without navigation
                        href = map_elements[0].get_attribute('href')
                        current_map_type = "Park Map"
                    else:
                        # Multiple elements found - navigate to each href for details
                        map_details_list = []
                        hrefs_to_check = []
                        for elem in map_elements:
                            hrefs_to_check.append(elem.get_attribute('href'))
                        for current_href in hrefs_to_check:
                            # Visit the href to get additional details
                            driver.get(current_href)
                            time.sleep(5)
                            
                            try:
                                date_element = driver.find_element(By.XPATH, "//div[contains(text(), 'Date Created:')]/following-sibling::div[1]")
                                date_timestamp = try_parsing_date_to_timestamp(date_element.text.strip())
                                print(date_timestamp)
                                
                                title_element = driver.find_element(By.XPATH, "//h1[@class='PhotoGalleryItem__Title page-title']")
                                map_title = title_element.text.strip().replace(" with Plan Oblique Relief", "")
                                print(map_title)
                                
                                map_details_list.append({
                                    'Title': map_title,
                                    'Date': date_timestamp,
                                    'URL': current_href
                                })
                            except Exception as e:
                                print(f"Error getting details for map: {str(e)}")
                        
                        try:
                            maps_df = pd.DataFrame(map_details_list)
                            # Keep only the most recent version of duplicate titles
                            maps_df = maps_df.sort_values('Date', ascending=False).drop_duplicates('Title', keep='first')
                            
                            href = " | ".join(maps_df['URL'].tolist())
                            current_map_type = "Multiple Park Maps" if len(maps_df) > 1 else "Park Map"
                        except Exception as e:
                            print(f"Error processing map details: {str(e)}")
                        
                        # Return to search page
                        driver.get("https://www.nps.gov/media/photo/collection.htm?pg=7323739&id=305fb7af-a71b-469b-941e-a98b439c882f&p=1&state=")
                        time.sleep(10)
                else:
                    raise Exception("No park maps found")
                    
            except Exception as e:
                try:
                    xpath_query = f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'area map')]{edge_case_xpath}"
                    map_elements = driver.find_elements(By.XPATH, xpath_query)
                    
                    if map_elements:
                        hrefs = [elem.get_attribute('href') for elem in map_elements]
                        href = " | ".join(hrefs)
                        current_map_type = "Multiple Area Maps" if len(hrefs) > 1 else "Area Map"
                        
                        # check if there are multiple unknown maps
                        other_maps_xpath_query = f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), ' map  - ') and not(contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'area map'))]{edge_case_xpath}"
                        try:
                            other_map_elements = driver.find_elements(By.XPATH, other_maps_xpath_query)
                            if other_map_elements and len(other_map_elements) > 1:
                                park_region_maps = []
                                for elem in other_map_elements:
                                    current_text = elem.text
                                    current_text = current_text.split(" map  - ")[0]
                                    current_href = elem.get_attribute('href')
                                    if any(word.lower() in park_region_words for word in current_text.split(" ")):
                                        park_region_maps.append(current_href)
                                
                                if len(park_region_maps) > 0:
                                    hrefs += park_region_maps
                                    href = " | ".join(hrefs)
                                    current_map_type = "Multiple Park Maps" if len(hrefs) > 1 else "Park Map"
                                # else just use the area map
                        except Exception as e:
                            print(f"Error processing other map elements. Area map will be used instead.")
                    else:
                        raise Exception("No area maps found")
                    
                except Exception as e:
                    try:
                        xpath_query = f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), ' map  - ')]{edge_case_xpath}"
                        map_elements = driver.find_elements(By.XPATH, xpath_query)
                        if map_elements:
                            park_region_maps = []
                            all_unknown_maps = []
                            for elem in map_elements:
                                current_text = elem.text
                                current_text = current_text.split(" map  - ")[0]
                                current_href = elem.get_attribute('href')
                                all_unknown_maps.append(current_href)
                                if any(word.lower() in park_region_words for word in current_text.split(" ")):
                                    park_region_maps.append(current_href)
                            
                            if len(park_region_maps) > 0:
                                href = " | ".join(park_region_maps)
                                current_map_type = "Multiple Park Maps" if len(park_region_maps) > 1 else "Park Map"
                            else:
                                href = " | ".join(all_unknown_maps)
                                current_map_type = "Multiple Unknown Maps" if len(all_unknown_maps) > 1 else "Unknown Map"
                        else:
                            href = "N/A"
                    except Exception as e:
                        print(f"Error processing unknown map elements: {str(e)}")
                        href = "N/A"

            print(href)
            print("Map Type: ", current_map_type)
            print("-" * 50)
            park_map_links.append(href)
            map_type.append(current_map_type)  # Append map type after all try-except blocks

        # Rename screenshot_dir to output_dir
        output_dir = os.path.join(os.path.expanduser("~"), "selenium-test")
        
        # Create the directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create the full screenshot path
        screenshot_path = os.path.join(output_dir, "nps_search_results.png")
        
        # Take the screenshot
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")

        # Create and save CSV file with park names and links
        csv_file_path = os.path.join(output_dir, "park_maps.csv")
        with open(csv_file_path, 'w') as f:
            f.write("Park Name,Map Link,Map Type\n")
            for park_name, link, map_type in zip(park_names, park_map_links, map_type):
                f.write(f"{park_name},{link},{map_type}\n")
        print(f"CSV file saved to: {csv_file_path}")

        #time.sleep(10)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        driver.quit()

# Add new code to read and format CSV
# Read the CSV file
csv_path = os.path.join(os.path.expanduser("~"), "selenium-test", "park_maps.csv")
df = pd.read_csv(csv_path)

# Filter for specified map types
mask = df['Map Type'].str.contains('Area|Multiple|Unknown', na=False)
filtered_df = df[mask]

# Print formatted results
print("Results for further review:")
print('-' * 75)
for _, row in filtered_df.iterrows():
    print(f"{row['Map Type']}: {row['Park Name']}")
    if row['Map Link'] != 'N/A':
        for link in row['Map Link'].split(' | '):
            print(link)
    print('-' * 75)