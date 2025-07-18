import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
import pandas as pd
from datetime import datetime
import random
import re

class MultiPropertyZillowScraper:
    def __init__(self, headless=False):
        self.all_properties_data = []
        self.last_scraped_url = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        try:
            import undetected_chromedriver as uc
            
            options = uc.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            
            # Enhanced anti-detection options
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Remove automation indicators
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
        except Exception as e:
            print(f"Failed to initialize undetected chrome: {e}")
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            if headless:
                options.add_argument("--headless")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
    
    def check_and_recover_driver(self):
        """Check if driver is still active and recover if needed"""
        try:
            self.driver.current_url
            return True
        except Exception as e:
            print(f"⚠️ Driver connection lost: {e}")
            print("🔄 Attempting to recover browser session...")
            
            try:
                self.driver.quit()
            except:
                pass
            
            self.setup_driver(headless=False)
            return True
        
    def navigate_to_search_page(self, search_url):
        """Navigate to search page with enhanced detection"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if not self.check_and_recover_driver():
                    continue
                    
                print(f"🔄 Navigating to search page (attempt {attempt + 1})...")
                self.driver.get(search_url)
                
                # Add random delay to mimic human behavior
                time.sleep(random.uniform(3, 6))
                
                # Wait for page to load and check for different possible containers
                page_loaded = False
                selectors_to_try = [
                    '[data-testid="search-page-list-container"]',
                    '#grid-search-results ul',
                    '[data-testid="property-card"]',
                    '.List-c11n-8-84-3__sc-1smrmqp-0',
                    '.search-page-list-container',
                    '.property-card-data'
                ]
                
                for selector in selectors_to_try:
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        print(f"✅ Successfully loaded search page with selector: {selector}")
                        page_loaded = True
                        break
                    except TimeoutException:
                        continue
                
                if page_loaded:
                    return True
                else:
                    print(f"❌ Failed to find search results on attempt {attempt + 1}")
                    # Take a screenshot for debugging
                    try:
                        self.driver.save_screenshot(f"debug_page_{attempt}.png")
                        print(f"📸 Screenshot saved: debug_page_{attempt}.png")
                    except:
                        pass
                    
                    if attempt < max_attempts - 1:
                        time.sleep(5)
                        continue
                
            except Exception as e:
                print(f"❌ Failed to load search page (attempt {attempt + 1}): {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
        
        return False

    def scrape_multiple_properties(self, search_url, max_properties=50):
        """Scrape multiple properties from search results with improved detection"""
        print(f"Starting to scrape {max_properties} properties from search results...")
        
        # Navigate to search page first
        if not self.navigate_to_search_page(search_url):
            print("❌ Failed to load search page, cannot proceed")
            return []
        
        properties_scraped = 0
        current_page = 1
        
        while properties_scraped < max_properties:
            print(f"\n=== PAGE {current_page} ===")
            
            # Get all property links on current page
            property_links = self.get_property_links()
            
            if not property_links:
                print("No property links found on this page.")
                # Try to take a screenshot for debugging
                try:
                    self.driver.save_screenshot(f"no_properties_page_{current_page}.png")
                    print(f"📸 Debug screenshot saved: no_properties_page_{current_page}.png")
                except:
                    pass
                break
            
            print(f"Found {len(property_links)} properties on page {current_page}")
            
            # Process each property on current page
            processed_urls = set()
            property_index = 0
            
            while property_index < len(property_links) and properties_scraped < max_properties:
                try:
                    print(f"\nProcessing property {properties_scraped + 1}/{max_properties} (Page {current_page}, Property {property_index + 1})")
                    
                    # Re-get property links to avoid stale element references
                    current_property_links = self.get_property_links()
                    if property_index >= len(current_property_links):
                        print(f"Property index {property_index} not available, moving to next page")
                        break
                    
                    link_element = current_property_links[property_index]
                    
                    # Get the href to check if we've already processed this property
                    try:
                        property_url = link_element.get_attribute('href')
                        if not property_url or property_url in processed_urls:
                            print(f"Already processed or invalid URL, moving to next")
                            property_index += 1
                            continue
                        
                        print(f"Processing property: {property_url}")
                        processed_urls.add(property_url)
                    except Exception as e:
                        print(f"Could not get property URL: {e}")
                        property_index += 1
                        continue
                    
                    # Navigate to property page
                    navigation_success = self.navigate_to_property(property_url)
                    
                    if not navigation_success:
                        print(f"❌ Failed to navigate to property")
                        property_index += 1
                        continue
                    
                    # Extract property data
                    property_data = self.extract_complete_property_data()
                    
                    if property_data:
                        self.all_properties_data.append(property_data)
                        properties_scraped += 1
                        print(f"✓ Successfully scraped property {properties_scraped}")
                    else:
                        print("✗ Failed to extract property data")
                    
                    # Navigate back to search results
                    if not self.go_back_to_search():
                        print("❌ Failed to return to search results, stopping")
                        break
                    
                    property_index += 1
                    time.sleep(random.uniform(1, 3))  # Random delay between properties
                    
                except Exception as e:
                    print(f"✗ Error processing property {property_index + 1}: {e}")
                    property_index += 1
                    
                    try:
                        self.go_back_to_search()
                    except:
                        print("❌ Critical navigation error, stopping scraper")
                        return self.all_properties_data
            
            # Check if we need to go to next page
            if properties_scraped < max_properties:
                print(f"\nFinished page {current_page}. Going to next page...")
                if not self.go_to_next_page():
                    print("No more pages available or failed to navigate. Stopping.")
                    break
                current_page += 1
                time.sleep(random.uniform(2, 4))
            
        print(f"\n🎉 Completed! Scraped {len(self.all_properties_data)} properties total.")
        return self.all_properties_data
    
    def get_property_links(self):
        """Get all clickable property links on current page with multiple strategies"""
        try:
            # Wait a bit for dynamic content to load
            time.sleep(2)
            
            # Try multiple selectors for property links
            selectors_to_try = [
                # New Zillow structure
                '[data-testid="property-card"] a',
                '.property-card-data a',
                '[data-testid="property-card-link"]',
                
                # Legacy selectors
                '#grid-search-results ul a[href*="/homedetails/"]',
                '.List-c11n-8-84-3__sc-1smrmqp-0 a',
                '.search-page-list-container a[href*="/homedetails/"]',
                
                # Generic fallbacks
                'a[href*="/homedetails/"]',
                'a[href*="zpid"]'
            ]
            
            property_links = []
            
            for selector in selectors_to_try:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"Found {len(elements)} links with selector: {selector}")
                        
                        # Filter for valid property links
                        valid_links = []
                        for element in elements:
                            try:
                                href = element.get_attribute('href')
                                if href and ('/homedetails/' in href or 'zpid' in href):
                                    valid_links.append(element)
                            except:
                                continue
                        
                        if valid_links:
                            property_links = valid_links
                            break
                except Exception as e:
                    continue
            
            # Remove duplicates based on href
            unique_links = {}
            for link in property_links:
                try:
                    href = link.get_attribute('href')
                    if href:
                        unique_links[href] = link
                except:
                    continue
            
            filtered_links = list(unique_links.values())
            print(f"Filtered to {len(filtered_links)} unique property links")
            
            return filtered_links
            
        except Exception as e:
            print(f"Error getting property links: {e}")
            return []
    
    def navigate_to_property(self, property_url):
        """Navigate to a specific property URL"""
        try:
            print(f"  Navigating to: {property_url}")
            self.driver.get(property_url)
            time.sleep(random.uniform(2, 4))
            
            # Verify we're on a property details page
            current_url = self.driver.current_url
            if "/homedetails/" in current_url or "zpid" in current_url:
                print(f"  ✓ Successfully navigated to property page")
                return True
            else:
                print(f"  ✗ Navigation failed - not on property page: {current_url}")
                return False
                
        except Exception as e:
            print(f"  ✗ Navigation error: {e}")
            return False
    
    def go_back_to_search(self):
        """Navigate back to search results"""
        try:
            print("Returning to search results...")
            self.driver.back()
            time.sleep(random.uniform(2, 4))
            
            # Verify we're back on search results
            selectors_to_check = [
                '[data-testid="search-page-list-container"]',
                '#grid-search-results',
                '.search-page-list-container',
                '[data-testid="property-card"]'
            ]
            
            for selector in selectors_to_check:
                try:
                    WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    print("✓ Back on search results page")
                    return True
                except TimeoutException:
                    continue
            
            print("✗ Failed to return to search results")
            return False
            
        except Exception as e:
            print(f"Error in go_back_to_search: {e}")
            return False
    
    def go_to_next_page(self):
        """Navigate to next page of results"""
        try:
            # Try multiple selectors for next page button
            next_page_selectors = [
                '[data-testid="pagination-next-page"]',
                'a[aria-label="Next page"]',
                'a[rel="next"]',
                '.PaginationJumpItem-c11n-8-84-3__sc-18hsrnn-0:last-child a',
                'nav [aria-label="Go to next page"]'
            ]
            
            for selector in next_page_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    
                    print(f"Found next page button with selector: {selector}")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    
                    time.sleep(random.uniform(3, 5))
                    return True
                    
                except:
                    continue
            
            print("No next page button found")
            return False
            
        except Exception as e:
            print(f"Error going to next page: {e}")
            return False
    
    def extract_complete_property_data(self):
        """Extract all property data from current property page"""
        try:
            print("Starting property data extraction...")
            
            property_data = {
                'url': self.driver.current_url,
                'scraped_at': datetime.now().isoformat(),
                
                'price': 'N/A',
                'beds': 'N/A', 
                'baths': 'N/A',
                'sqft': 'N/A',
                'sqft_lot': 'N/A',
                'address': 'N/A',
                'estimated_monthly_payment': 'N/A',
                'property_type': 'N/A',
                'price_per_sqft': 'N/A',
                'year_built': 'N/A',
                'region': 'N/A',
                
                'interior_features': [],
                'other_rooms': [],
                'appliances': [],
                'utilities': 'N/A',
                'parking': 'N/A',
                
                'walk_score': 'N/A',
                'bike_score': 'N/A',
                
                'elementary_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
                'middle_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
                'high_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
    
                'flood_risk': 'N/A',
                'fire_risk': 'N/A',
                'wind_risk': 'N/A',
                'air_risk': 'N/A',
                'heat_risk': 'N/A',

                'nearby_cities': [],
                'property_history': 'N/A'
            }
            
            # Extract basic property information
            self.extract_basic_property_info(property_data)
            
            # Extract additional features
            self.extract_property_features(property_data)
            
            # Extract neighborhood and risk data
            self.extract_neighborhood_data(property_data)
            
            print("Property data extraction completed!")
            return property_data
            
        except Exception as e:
            print(f"Error in extraction: {e}")
            return None
    
    def extract_basic_property_info(self, property_data):
        """Extract basic property information"""
        try:
            # Extract price
            price_selectors = [
                '[data-testid="price"]',
                '.notranslate',
                'span[class*="Text"][class*="notranslate"]'
            ]
            
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    if '$' in price_text and re.match(r'^\$[\d,]+', price_text):
                        property_data['price'] = price_text
                        break
                except:
                    continue
            
            # Extract address
            address_selectors = [
                'h1[data-testid="street-address"]',
                '[data-testid="street-address"]',
                'h1'
            ]
            
            for selector in address_selectors:
                try:
                    address_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    address_text = address_element.text.strip()
                    if any(indicator in address_text.lower() for indicator in ['st', 'ave', 'rd', 'dr', 'ma']):
                        property_data['address'] = address_text
                        break
                except:
                    continue
            
            # Extract beds, baths, sqft from page text
            page_text = self.driver.page_source
            
            # Look for bed/bath/sqft pattern
            bed_bath_sqft_pattern = re.compile(r'(\d+)\s*(bed|bd|bedroom)s?\s*[,•·]?\s*(\d+(?:\.\d+)?)\s*(bath|ba|bathroom)s?\s*[,•·]?\s*([\d,]+)\s*(sqft|sq\.?\s*ft)', re.I)
            match = bed_bath_sqft_pattern.search(page_text)
            
            if match:
                property_data['beds'] = match.group(1)
                property_data['baths'] = match.group(3)
                property_data['sqft'] = match.group(5)
            else:
                # Try individual patterns
                bed_match = re.search(r'(\d+)\s*(bed|bd|bedroom)s?', page_text, re.I)
                if bed_match:
                    property_data['beds'] = bed_match.group(1)
                
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(bath|ba|bathroom)s?', page_text, re.I)
                if bath_match:
                    property_data['baths'] = bath_match.group(1)
                
                sqft_match = re.search(r'([\d,]+)\s*(sqft|sq\.?\s*ft)', page_text, re.I)
                if sqft_match:
                    property_data['sqft'] = sqft_match.group(1)
            
        except Exception as e:
            print(f"Error extracting basic info: {e}")
    
    def extract_property_features(self, property_data):
        """Extract property features and details"""
        try:
            page_text = self.driver.page_source
            
            # Extract interior features
            interior_features = []
            feature_patterns = [
                r'hardwood\s+floors?', r'granite\s+countertops?', r'stainless\s+steel',
                r'fireplace', r'walk-in\s+closet', r'tile\s+floors?'
            ]
            
            for pattern in feature_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:3]:
                    if match.lower() not in [f.lower() for f in interior_features]:
                        interior_features.append(match)
            
            property_data['interior_features'] = interior_features
            
            # Extract year built
            year_match = re.search(r'Built in (\d{4})', page_text, re.I)
            if year_match:
                property_data['year_built'] = year_match.group(1)
            
            # Extract price per sqft
            price_sqft_match = re.search(r'\$([\d,]+)/sqft', page_text, re.I)
            if price_sqft_match:
                property_data['price_per_sqft'] = f"${price_sqft_match.group(1)}/sqft"
            
        except Exception as e:
            print(f"Error extracting features: {e}")
    
    def extract_neighborhood_data(self, property_data):
        """Extract neighborhood scores and school information"""
        try:
            page_text = self.driver.page_source
            
            # Extract walk score
            walk_score_match = re.search(r'Walk Score[®]?\s*(\d+)', page_text, re.I)
            if walk_score_match:
                property_data['walk_score'] = f"{walk_score_match.group(1)}/100"
            
            # Extract bike score
            bike_score_match = re.search(r'Bike Score[®]?\s*(\d+)', page_text, re.I)
            if bike_score_match:
                property_data['bike_score'] = f"{bike_score_match.group(1)}/100"
            
        except Exception as e:
            print(f"Error extracting neighborhood data: {e}")
    
    def save_all_properties(self, filename_prefix="massachusetts_properties"):
        """Save all scraped properties to JSON and CSV"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.all_properties_data:
            # Save to JSON
            json_filename = f"{filename_prefix}_{timestamp}.json"
            with open(json_filename, 'w') as f:
                json.dump(self.all_properties_data, f, indent=2)
            
            # Save to CSV
            csv_filename = f"{filename_prefix}_{timestamp}.csv"
            flattened_data = []
            for property_data in self.all_properties_data:
                flattened_data.append(self.flatten_property_data(property_data))
            
            df = pd.DataFrame(flattened_data)
            df.to_csv(csv_filename, index=False)
            
            print(f"\n📁 All properties saved:")
            print(f"   • {json_filename} (structured)")
            print(f"   • {csv_filename} (flattened)")
            print(f"   • Total properties: {len(self.all_properties_data)}")
            
            return json_filename, csv_filename
        else:
            print("No properties data to save")
            return None, None
    
    def flatten_property_data(self, data):
        """Flatten nested data for CSV export"""
        flattened = {}
        
        for key, value in data.items():
            if isinstance(value, list):
                flattened[key] = '; '.join(str(item) for item in value)
            elif isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, dict):
                        for deep_key, deep_value in nested_value.items():
                            flattened[f"{key}_{nested_key}_{deep_key}"] = deep_value
                    else:
                        flattened[f"{key}_{nested_key}"] = nested_value
            else:
                flattened[key] = value
        
        return flattened

if __name__ == "__main__":
    import os
    
    print("="*80)
    print("IMPROVED ZILLOW SCRAPER")
    print("="*80)
    
    # Configuration
    max_properties = int(os.getenv('MAX_PROPERTIES', '10'))  # Start with fewer for testing
    search_location = os.getenv('SEARCH_LOCATION', 'ma')
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    print(f"Configuration:")
    print(f"  • Max properties: {max_properties}")
    print(f"  • Search location: {search_location}")
    print(f"  • Headless mode: {headless}")
    print("="*80)
    
    # Build search URL
    if search_location == 'ma':
        search_url = "https://www.zillow.com/ma/"
    else:
        search_url = f"https://www.zillow.com/homes/for_sale/{search_location}/"
    
    print(f"Search URL: {search_url}")
    
    # Initialize scraper
    scraper = MultiPropertyZillowScraper(headless=headless)
    
    try:
        # Scrape properties
        print(f"\nStarting to scrape {max_properties} properties...")
        all_properties = scraper.scrape_multiple_properties(search_url, max_properties=max_properties)
        
        # Save all data
        if all_properties:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file, csv_file = scraper.save_all_properties(
                filename_prefix=f"zillow_{search_location}_{timestamp}"
            )
            
            print(f"\n🎯 SCRAPING COMPLETE!")
            print(f"   ✓ Successfully scraped: {len(all_properties)} properties")
            print(f"   ✓ Data saved to: {json_file}")
            print(f"   ✓ CSV saved to: {csv_file}")
            
        else:
            print("\n❌ No properties were scraped successfully")
    
    except KeyboardInterrupt:
        print("\n⏹️ Scraping interrupted by user")
        if scraper.all_properties_data:
            print("Saving partial data...")
            scraper.save_all_properties(filename_prefix=f"zillow_{search_location}_partial")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if scraper.all_properties_data:
            print("Saving partial data...")
            scraper.save_all_properties(filename_prefix=f"zillow_{search_location}_error")
    
    finally:
        # Clean up
        try:
            scraper.driver.quit()
        except:
            pass
    
    print("\n" + "="*80)
    print("SCRAPING SESSION ENDED")
    print("="*80)
