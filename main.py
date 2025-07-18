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
        self.last_scraped_url = None  # Track last scraped URL to avoid duplicates
        self.setup_driver(headless)

    def setup_driver(self, headless):
        try:
            import undetected_chromedriver as uc
            
            options = uc.ChromeOptions()
            
            # Enhanced anti-detection options for GitHub Actions
            if headless:
                options.add_argument("--headless=new")
            
            # Essential options for GitHub Actions
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")  # Speed up loading
            options.add_argument("--disable-javascript-harmony-shipping")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")
            options.add_argument("--hide-scrollbars")
            options.add_argument("--mute-audio")
            options.add_argument("--no-first-run")
            options.add_argument("--safebrowsing-disable-auto-update")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            
            # User agent to appear more legitimate
            options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Additional stealth options
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            # Removed the problematic "detach" option for GitHub Actions
            
            print("Setting up undetected Chrome driver...")
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # Execute script to remove webdriver traces
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✓ Chrome driver setup completed")
            
        except Exception as e:
            print(f"Undetected Chrome failed: {e}")
            print("Falling back to regular Chrome...")
            
            from webdriver_manager.chrome import ChromeDriverManager
            from selenium.webdriver.chrome.service import Service
            
            options = Options()
            if headless:
                options.add_argument("--headless=new")
            
            # Same options as above
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver traces
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    
    # Also add this improved method to handle Zillow's page loading
    
    def navigate_to_search_page_improved(self, search_url):
        """Enhanced navigation with better error handling"""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                print(f"🔄 Navigating to search page (attempt {attempt + 1})...")
                
                # Clear cookies and cache
                self.driver.delete_all_cookies()
                
                # Navigate to Zillow homepage first
                print("  - Loading Zillow homepage...")
                self.driver.get("https://www.zillow.com")
                time.sleep(3)
                
                # Then navigate to search page
                print(f"  - Loading search page: {search_url}")
                self.driver.get(search_url)
                time.sleep(5)
                
                # Wait longer and try multiple selectors
                search_selectors = [
                    '//*[@id="grid-search-results"]/ul',
                    '//*[@id="grid-search-results"]',
                    '//ul[contains(@class, "photo-cards")]',
                    '//div[contains(@class, "search-page-react-content")]',
                    '//article[contains(@class, "property-card")]'
                ]
                
                found_results = False
                for selector in search_selectors:
                    try:
                        print(f"  - Trying selector: {selector}")
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        print(f"  ✓ Found search results with selector: {selector}")
                        found_results = True
                        break
                    except:
                        continue
                
                if found_results:
                    print("✅ Successfully loaded search page")
                    return True
                else:
                    print("❌ No search results found with any selector")
                    # Save page source for debugging
                    with open(f"debug_page_{attempt}.html", "w") as f:
                        f.write(self.driver.page_source)
                    print(f"  - Saved page source to debug_page_{attempt}.html")
                    
            except Exception as e:
                print(f"❌ Failed to load search page (attempt {attempt + 1}): {e}")
                
            if attempt < max_attempts - 1:
                print("  - Waiting before retry...")
                time.sleep(5)
        
        return False
    
    def check_and_recover_driver(self):
        """Check if driver is still active and recover if needed"""
        try:
            # Simple check to see if driver is responsive
            self.driver.current_url
            return True
        except Exception as e:
            print(f"⚠️ Driver connection lost: {e}")
            print("🔄 Attempting to recover browser session...")
            
            try:
                # Try to quit the existing driver
                self.driver.quit()
            except:
                pass
            
            # Reinitialize the driver
            self.setup_driver(headless=False)
            return True
        


    def scrape_multiple_properties(self, search_url, max_properties=50):
        """Scrape multiple properties from search results"""
        print(f"Starting to scrape {max_properties} properties from search results...")
        
        self.driver.get(search_url)
        time.sleep(5)
        
        properties_scraped = 0
        current_page = 1
        search_base_url = search_url  # Store original search URL
        
        while properties_scraped < max_properties:
            print(f"\n=== PAGE {current_page} ===")
            
            # Wait for search results to load
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
                )
                print("Search results container found")
            except TimeoutException:
                print("Search results not found. Stopping.")
                break
            
            # Get all property links on current page
            property_links = self.get_property_links()
            
            if not property_links:
                print("No property links found on this page.")
                break
            
            print(f"Found {len(property_links)} properties on page {current_page}")
            
            # Track processed properties on this page by their href
            processed_urls = set()
            property_index = 0
            max_attempts_per_property = 3  # Maximum attempts to find a new property
            
            # Process each property on current page
            while property_index < len(property_links) and properties_scraped < max_properties:
                attempts = 0
                found_new_property = False
                
                while attempts < max_attempts_per_property and not found_new_property:
                    try:
                        print(f"\nProcessing property {properties_scraped + 1}/{max_properties} (Page {current_page}, Property {property_index + 1}, Attempt {attempts + 1})")
                        
                        # Re-get property links to avoid stale element references
                        current_property_links = self.get_property_links()
                        if property_index >= len(current_property_links):
                            print(f"Property index {property_index} not available, moving to next page")
                            property_index = len(property_links)  # Force exit from while loop
                            break
                        
                        link_element = current_property_links[property_index]
                        
                        # Get the href to check if we've already processed this property
                        try:
                            property_url = link_element.get_attribute('href')
                            if property_url in processed_urls:
                                print(f"Already processed this property, moving to next: {property_url}")
                                property_index += 1
                                attempts = 0  # Reset attempts for next property
                                break
                            
                            print(f"Clicking on property {property_index + 1}: {property_url}")
                            processed_urls.add(property_url)
                            found_new_property = True
                        except Exception as e:
                            print(f"Could not get property URL: {e}")
                            property_index += 1
                            attempts = 0
                            break
                        
                        # Store current URL before navigation
                        current_url_before = self.driver.current_url
                        
                        # Try multiple navigation methods
                        navigation_success = False
                        
                        # Method 1: Direct URL navigation (most reliable)
                        try:
                            print(f"  Method 1: Direct navigation to {property_url}")
                            self.driver.get(property_url)
                            time.sleep(random.uniform(2, 4))
                            
                            # Verify we navigated to the correct property
                            if property_url in self.driver.current_url or "/homedetails/" in self.driver.current_url:
                                if self.driver.current_url != current_url_before:
                                    navigation_success = True
                                    print(f"  ✓ Successfully navigated via direct URL")
                                else:
                                    print(f"  ✗ URL didn't change from previous page")
                            else:
                                print(f"  ✗ Direct navigation failed")
                        except Exception as e:
                            print(f"  ✗ Direct navigation error: {e}")
                        
                        # Method 2: JavaScript click with better verification
                        if not navigation_success:
                            try:
                                print(f"  Method 2: JavaScript click")
                                # Scroll to element first
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
                                time.sleep(1)
                                
                                # Click using JavaScript
                                self.driver.execute_script("arguments[0].click();", link_element)
                                time.sleep(random.uniform(1, 3))
                                
                                # Verify navigation
                                if "/homedetails/" in self.driver.current_url and self.driver.current_url != current_url_before:
                                    navigation_success = True
                                    print(f"  ✓ Successfully navigated via JavaScript click")
                                else:
                                    print(f"  ✗ JavaScript click didn't navigate properly")
                            except Exception as e:
                                print(f"  ✗ JavaScript click error: {e}")
                        
                        # Method 3: ActionChains click
                        if not navigation_success:
                            try:
                                print(f"  Method 3: ActionChains click")
                                # Re-find the element to avoid stale reference
                                current_property_links = self.get_property_links()
                                if property_index < len(current_property_links):
                                    fresh_link = current_property_links[property_index]
                                    
                                    actions = ActionChains(self.driver)
                                    actions.move_to_element(fresh_link).click().perform()
                                    time.sleep(random.uniform(1, 3))
                                    
                                    # Verify navigation
                                    if "/homedetails/" in self.driver.current_url and self.driver.current_url != current_url_before:
                                        navigation_success = True
                                        print(f"  ✓ Successfully navigated via ActionChains")
                                    else:
                                        print(f"  ✗ ActionChains click didn't navigate properly")
                            except Exception as e:
                                print(f"  ✗ ActionChains click error: {e}")
                        
                        # Final verification
                        if not navigation_success:
                            print(f"  ❌ All navigation methods failed for property {property_index + 1}")
                            property_index += 1
                            attempts = 0
                            continue
                        
                        # Double-check we're on the right property page
                        final_url = self.driver.current_url
                        if "/homedetails/" not in final_url:
                            print(f"  ❌ Not on a property details page: {final_url}")
                            self.go_back_to_search()
                            property_index += 1
                            attempts = 0
                            continue
                        
                        # Verify we're not on the same property as before
                        if hasattr(self, 'last_scraped_url') and self.last_scraped_url == final_url:
                            print(f"  ⚠️  Same property as last time, skipping: {final_url}")
                            self.go_back_to_search()
                            property_index += 1
                            attempts = 0
                            continue
                        
                        # Store this URL for next comparison
                        self.last_scraped_url = final_url
                        
                        # Extract property data with timeout (Windows-compatible)
                        print(f"Successfully navigated to property page: {self.driver.current_url}")
                        
                        # Add URL validation before extraction
                        current_property_url = self.driver.current_url
                        if not current_property_url or "/homedetails/" not in current_property_url:
                            print(f"❌ Invalid property URL: {current_property_url}")
                            self.go_back_to_search()
                            property_index += 1
                            attempts = 0
                            continue
                        
                        try:
                            # Simple timeout without signal (Windows compatible)
                            import threading
                            import time as time_module
                            
                            def extract_with_timeout():
                                return self.extract_complete_property_data()
                            
                            # Create a thread for extraction
                            result = [None]
                            exception = [None]
                            
                            def run_extraction():
                                try:
                                    result[0] = extract_with_timeout()
                                except Exception as e:
                                    exception[0] = e
                            
                            thread = threading.Thread(target=run_extraction)
                            thread.daemon = True
                            thread.start()
                            thread.join(timeout=45)  # 45 second timeout
                            
                            if thread.is_alive():
                                print("⚠️ Property extraction timed out after 45 seconds, skipping...")
                                property_data = None
                            elif exception[0]:
                                print(f"⚠️ Error during property extraction: {exception[0]}")
                                property_data = None
                            else:
                                property_data = result[0]
                            
                        except Exception as e:
                            print(f"⚠️ Error during property extraction: {e}")
                            property_data = None
                        
                        if property_data:
                            self.all_properties_data.append(property_data)
                            properties_scraped += 1
                            print(f"✓ Successfully scraped property {properties_scraped}")
                        else:
                            print("✗ Failed to extract property data")
                        
                        # Navigate back to search results
                        print("Going back to search results...")
                        self.go_back_to_search()
                        
                        # Wait for search results to reload
                        time.sleep(1.5)
                        
                        # Verify we're back on search results
                        try:
                            WebDriverWait(self.driver, 8).until(
                                EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
                            )
                            print("✓ Back on search results page")
                        except TimeoutException:
                            print("✗ Failed to return to search results")
                            break
                        
                        # Move to next property
                        property_index += 1
                        attempts = 0  # Reset attempts for next property
                        
                    except Exception as e:
                        print(f"✗ Error processing property {property_index + 1}: {e}")
                        attempts += 1
                        if attempts >= max_attempts_per_property:
                            print(f"Max attempts reached for property {property_index + 1}, moving to next")
                            property_index += 1
                            attempts = 0
                        
                        # Try to go back to search results anyway
                        try:
                            back_success = self.go_back_to_search()
                            if not back_success:
                                print("❌ Failed to return to search results after error, stopping")
                                return self.all_properties_data
                            time.sleep(2)
                        except:
                            print("❌ Critical navigation error, stopping scraper")
                            return self.all_properties_data
            
            # Check if we need to go to next page
            if properties_scraped < max_properties:
                print(f"\nFinished page {current_page} (processed {len(processed_urls)} properties). Going to next page...")
                if not self.go_to_next_page():
                    print("No more pages available or failed to navigate. Stopping.")
                    break
                current_page += 1
                time.sleep(1)
            
        print(f"\n🎉 Completed! Scraped {len(self.all_properties_data)} properties total.")
        return self.all_properties_data
    
    def get_property_links(self):
        """Get all clickable property links on current page"""
        try:
            # Wait for the results container with longer timeout
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
            )
            
            # Find property links specifically in the grid results
            property_links = self.driver.find_elements(By.XPATH, '//*[@id="grid-search-results"]/ul//a[contains(@href, "/homedetails/")]')
            
            print(f"Found {len(property_links)} property links using primary selector")
            
            # If no links found, try alternative selectors
            if not property_links:
                alternative_selectors = [
                    '//*[@id="grid-search-results"]/ul//article//a',
                    '//*[@id="grid-search-results"]//a[contains(@href, "zpid")]',
                    '//*[@id="grid-search-results"]/ul//a'
                ]
                
                for selector in alternative_selectors:
                    property_links = self.driver.find_elements(By.XPATH, selector)
                    if property_links:
                        print(f"Found {len(property_links)} property links using alternative selector: {selector}")
                        break
            
            # Filter out any non-property links and get unique URLs
            unique_links = {}  # Use dict to maintain order and ensure uniqueness
            for link in property_links:
                try:
                    href = link.get_attribute('href')
                    if href and ('/homedetails/' in href or 'zpid' in href):
                        # Use href as key to avoid duplicates
                        unique_links[href] = link
                except:
                    continue
            
            filtered_links = list(unique_links.values())
            print(f"Filtered to {len(filtered_links)} unique property links")
            return filtered_links
            
        except Exception as e:
            print(f"Error getting property links: {e}")
            return []
    
    def go_back_to_search(self):
        """Navigate back to search results using multiple strategies"""
        try:
            print("Attempting to return to search results...")
            
            # Store current URL for verification
            current_url = self.driver.current_url
            
            # Strategy 1: Browser back (most reliable for this case)
            try:
                print("  Strategy 1: Using browser back")
                self.driver.back()
                time.sleep(3)
                
                # Wait for search results to appear
                try:
                    WebDriverWait(self.driver, 8).until(
                        EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
                    )
                    print("  ✓ Successfully returned to search results via browser back")
                    return True
                except TimeoutException:
                    print("  ✗ Browser back didn't return to search results")
            except Exception as e:
                print(f"  ✗ Browser back failed: {e}")
            
            # Strategy 2: Try specific back button selectors
            back_button_selectors = [
                '//*[@id="wrapper"]/div[2]/div[1]/section/div/div[1]/div/nav/div/span/button',
                '//button[contains(@aria-label, "Back to search")]',
                '//button[contains(@aria-label, "Back")]',
                '//button[contains(text(), "Back")]',
                '//nav//button[contains(@class, "back")]'
            ]
            
            for selector in back_button_selectors:
                try:
                    print(f"  Strategy 2: Trying back button selector: {selector}")
                    back_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    self.driver.execute_script("arguments[0].click();", back_button)
                    time.sleep(3)
                    
                    # Verify we're back on search results
                    try:
                        WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
                        )
                        print("  ✓ Successfully returned to search results via back button")
                        return True
                    except TimeoutException:
                        continue
                        
                except Exception as e:
                    continue
            
            # Strategy 3: Navigate to Massachusetts search URL directly
            print("  Strategy 3: Direct navigation to search page")
            try:
                search_url = "https://www.zillow.com/ma/"
                self.driver.get(search_url)
                time.sleep(2)
                
                # Wait for search results
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="grid-search-results"]/ul'))
                )
                print("  ✓ Successfully returned to search results via direct navigation")
                return True
                
            except Exception as e:
                print(f"  ✗ Direct navigation failed: {e}")
            
            print("  ❌ All navigation strategies failed")
            return False
            
        except Exception as e:
            print(f"Error in go_back_to_search: {e}")
            return False
    
    def go_to_next_page(self):
        """Navigate to next page of results"""
        try:
            # Wait for current page to load completely
            time.sleep(1)
            
            # Try your specific next page xpath first
            next_page_selectors = [
                '/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/div[2]/nav/ul/li[10]',
                '/html/body/div[1]/div/div[2]/div/div/div[1]/div[1]/div[2]/nav/ul/li[10]/a',
                '//*[@id="grid-search-results"]/div[2]/nav/ul/li[10]/a',
                '//*[@id="grid-search-results"]/div[2]/nav/ul/li[10]'
            ]
            
            for selector in next_page_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    print(f"Found next page button with selector: {selector}")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    
                    # Wait for new page to load
                    time.sleep(2)
                    return True
                    
                except:
                    continue
            
            # Try alternative next page selectors
            alternative_selectors = [
                '//nav//a[contains(@aria-label, "Next page")]',
                '//nav//a[contains(text(), "Next")]',
                '//a[@rel="next"]',
                '//button[contains(@aria-label, "Next page")]',
                '//*[@id="grid-search-results"]//nav//a[contains(@class, "next")]',
                '//nav//li[last()]//a',
                '//nav//li[contains(@class, "next")]//a'
            ]
            
            for selector in alternative_selectors:
                try:
                    next_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    print(f"Found alternative next button: {selector}")
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", next_button)
                    
                    # Wait for new page to load
                    time.sleep(2)
                    return True
                except:
                    continue
            
            print("No next page button found")
            return False
            
        except Exception as e:
            print(f"Error going to next page: {e}")
            return False
    
    def extract_complete_property_data(self):
        """Extract all property data from current property page - optimized version"""
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
                'region':'N/A',
                
                'interior_features': [],
                'other_rooms': [],
                'appliances': [],
                'utilities': 'N/A',
                'parking': 'N/A',
                
                'walk_score':'N/A',
                'bike_score':'N/A',
                
                'elementary_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
                'middle_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
                'high_school': {'name': 'N/A', 'score': 'N/A', 'distance': 'N/A'},
    
                'flood_risk': 'N/A',
                'fire_risk': 'N/A',
                'wind_risk':'N/A',
                'air_risk':'N/A',
                'heat_risk': 'N/A',

                'nearby_cities': [],
                'property_history': 'N/A'
            }
            
            # Only extract essential data quickly
            print("Extracting basic info...")
            try:
                self.extract_price_and_basic_info(property_data)
            except Exception as e:
                print(f"  - Error in basic info: {e}")
            
            print("Extracting property features...")
            try:
                self.extract_property_features_detailed(property_data)
            except Exception as e:
                print(f"  - Error in features: {e}")
                
            self.extract_neighborhood_scores_detailed(property_data)
            self.extract_schools_detailed(property_data)
            self.extract_environmental_risks(property_data)
            self.extract_market_data_detailed(property_data)
            self.extract_monthly_payment(property_data)
            self.extract_nearby_cities(property_data)
            
            print("Property data extraction completed!")
            return property_data
            
        except Exception as e:
            print(f"Error in extraction: {e}")
            return None
    
    def extract_price_and_basic_info(self, property_data):
        self.extract_price_advanced(property_data)
        self.extract_basic_info_advanced(property_data)
    
    def extract_price_advanced(self, property_data):
        price_strategies = [
            ('CSS', 'span[data-testid="price"]'),
            ('CSS', '.notranslate'),
            ('CSS', 'h3 span'),
            ('CSS', 'span.Text-c11n-8-100-1__sc-aiai24-0'),
            ('XPATH', "//span[contains(@class, 'Text') and contains(text(), '$')]"),
            ('XPATH', "//h3//span[contains(text(), '$')]"),
        ]
        
        for strategy_type, selector in price_strategies:
            try:
                if strategy_type == 'CSS':
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                else:
                    elements = self.driver.find_elements(By.XPATH, selector)
                
                for element in elements:
                    text = element.text.strip()
                    price_match = re.match(r'^\$[\d,]+(?:\.\d{2})?$', text)
                    if price_match:
                        property_data['price'] = text
                        return
            except:
                continue
    
    def extract_basic_info_advanced(self, property_data):
        all_elements = self.driver.find_elements(By.XPATH, "//span | //div")
        
        bed_bath_sqft_pattern = re.compile(r'(\d+)\s*(bed|bd|bedroom|br)s?\s*[,•·]?\s*(\d+(?:\.\d+)?)\s*(bath|ba|bathroom)s?\s*[,•·]?\s*([\d,]+)\s*(sqft|sq\.?\s*ft)', re.I)
        
        for element in all_elements:
            text = element.text.strip()
            
            match = bed_bath_sqft_pattern.search(text)
            if match:
                property_data['beds'] = match.group(1)
                property_data['baths'] = match.group(3)
                property_data['sqft'] = match.group(5)
                break
            
            if property_data['beds'] == 'N/A':
                bed_match = re.search(r'(\d+)\s*(bed|bd|bedroom|br)s?', text, re.I)
                if bed_match and int(bed_match.group(1)) <= 10:
                    property_data['beds'] = bed_match.group(1)
            
            if property_data['baths'] == 'N/A':
                bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(bath|ba|bathroom)s?', text, re.I)
                if bath_match and float(bath_match.group(1)) <= 10:
                    property_data['baths'] = bath_match.group(1)
            
            if property_data['sqft'] == 'N/A':
                sqft_match = re.search(r'([\d,]+)\s*(sqft|sq\.?\s*ft)', text, re.I)
                if sqft_match:
                    sqft_value = int(sqft_match.group(1).replace(',', ''))
                    if 300 <= sqft_value <= 20000:
                        property_data['sqft'] = sqft_match.group(1)
        
        address_strategies = [
            ('CSS', 'h1[data-testid="street-address"]'),
            ('CSS', 'h1'),
        ]
        
        for strategy_type, selector in address_strategies:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if any(indicator in text.lower() for indicator in ['st', 'ave', 'rd', 'dr', 'ma']):
                    property_data['address'] = text
                    break
            except:
                continue
        
        page_text = self.driver.page_source
        
        type_match = re.search(r'(single.family|condo|townhouse|multi.family)', page_text, re.I)
        if type_match:
            property_data['property_type'] = type_match.group(1)
        
        year_patterns = [
            r'Built in (\d{4})',
            r'built[:\s]+(\d{4})',
            r'year[:\s]+(\d{4})'
        ]
        for pattern in year_patterns:
            year_match = re.search(pattern, page_text, re.I)
            if year_match:
                property_data['year_built'] = year_match.group(1)
                break
        
        price_sqft_patterns = [
            r'\$([\d,]+)/sqft',
            r'\$([\d,]+)\s*price/sqft',
            r'price/sqft[:\s]+\$([\d,]+)',
            r'\$([\d,]+)\s*/\s*sqft'
        ]
        for pattern in price_sqft_patterns:
            price_sqft_match = re.search(pattern, page_text, re.I)
            if price_sqft_match:
                price_value = price_sqft_match.group(1).replace(',', '')
                property_data['price_per_sqft'] = f"${price_value}/sqft"
                break
        
        lot_patterns = [
            r'(\d+\.?\d*)\s*Acres',
            r'lot[:\s]*([\d,.]+)\s*(sq\s*ft|acres)',
            r'([\d,.]+)\s*(acres|sq\s*ft)\s*lot'
        ]
        
        for pattern in lot_patterns:
            lot_match = re.search(pattern, page_text, re.I)
            if lot_match:
                size = lot_match.group(1)
                if 'acres' in lot_match.group(0).lower():
                    property_data['sqft_lot'] = f"{size} Acres"
                else:
                    property_data['sqft_lot'] = f"{size} sqft"
                break

    def extract_property_features_detailed(self, property_data):
        try:
            print("  - Scrolling to middle of page...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            
            print("  - Looking for expandable buttons...")
            try:
                expandable_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'See more') or contains(text(), 'Show more') or contains(text(), 'Facts')]")
                for i, button in enumerate(expandable_buttons[:3]):  # Limit to first 3 buttons
                    try:
                        print(f"    - Clicking button {i+1}")
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(0.5)
                    except:
                        pass
            except Exception as e:
                print(f"    - No expandable buttons found: {e}")
            
            print("  - Extracting features from page source...")
            page_text = self.driver.page_source
            
            interior_features = []
            feature_patterns = [
                r'hardwood\s+floors?', r'granite\s+countertops?', r'stainless\s+steel', r'tile\s+floors?',
                r'carpet', r'laminate', r'marble', r'walk-in\s+closet', r'bay\s+window', r'skylight',
                r'fireplace', r'built-in\s+shelves?', r'crown\s+molding', r'vaulted\s+ceiling'
            ]
            
            for pattern in feature_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:5]:
                    if match.lower() not in [f.lower() for f in interior_features]:
                        interior_features.append(match)
            
            property_data['interior_features'] = interior_features
            
            room_patterns = [
                r'dining\s+room', r'family\s+room', r'living\s+room', r'bonus\s+room', r'office',
                r'den', r'study', r'library', r'sunroom', r'basement', r'attic', r'laundry\s+room',
                r'mud\s+room', r'pantry', r'walk-in\s+pantry'
            ]
            
            other_rooms = []
            for pattern in room_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:3]:
                    if match.lower() not in [r.lower() for r in other_rooms]:
                        other_rooms.append(match)
            
            property_data['other_rooms'] = other_rooms
            
            appliance_patterns = [
                r'dishwasher', r'refrigerator', r'microwave', r'oven', r'range', r'cooktop',
                r'disposal', r'washer', r'dryer', r'freezer', r'wine\s+cooler', r'ice\s+maker'
            ]
            
            appliances = []
            for pattern in appliance_patterns:
                matches = re.findall(pattern, page_text, re.I)
                for match in matches[:3]:
                    if match.lower() not in [a.lower() for a in appliances]:
                        appliances.append(match)
            
            property_data['appliances'] = appliances
            
            utilities = {}
            utility_patterns = {
                'Electric': r'Electric:\s*([^<\n]+)',
                'Sewer': r'Sewer:\s*([^<\n]+)', 
                'Water': r'Water:\s*([^<\n]+)',
                'Utilities': r'Utilities for property:\s*([^<\n]+)'
            }
            
            for utility_type, pattern in utility_patterns.items():
                match = re.search(pattern, page_text, re.I)
                if match:
                    utilities[utility_type] = match.group(1).strip()
            
            property_data['utilities'] = utilities
            
            parking = {}
            parking_patterns = {
                'total_spaces': r'Total spaces:\s*(\d+)',
                'garage_spaces': r'Garage spaces:\s*(\d+)',
                'parking_features': r'Parking features:\s*([^<\n]+)',
                'uncovered_spaces': r'Has uncovered spaces:\s*([^<\n]+)'
            }
            
            for parking_type, pattern in parking_patterns.items():
                match = re.search(pattern, page_text, re.I)
                if match:
                    parking[parking_type] = match.group(1).strip()
            
            property_data['parking'] = parking
            print("  - Features extraction completed")
            
        except Exception as e:
            print(f"  - Error in features extraction: {e}")
            property_data['interior_features'] = []
            property_data['other_rooms'] = []
            property_data['appliances'] = []
            property_data['utilities'] = 'N/A'
            property_data['parking'] = 'N/A'
    
    def extract_neighborhood_scores_detailed(self, property_data):
        try:
            print("  - Looking for neighborhood scores...")
            try:
                getting_around_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Getting around')]")
                if getting_around_elements:
                    self.driver.execute_script("arguments[0].scrollIntoView();", getting_around_elements[0])
                    time.sleep(1)
            except:
                pass
            
            page_text = self.driver.page_source
            
            walk_score_patterns = [
                r'Walk Score[®]?\s*(\d+)\s*/\s*100',
                r'Walk Score[®]?\s*(\d+)\s*\/\s*100',
                r'Walk Score[®]?[^0-9]*(\d+)',
            ]
            
            for pattern in walk_score_patterns:
                walk_match = re.search(pattern, page_text, re.I)
                if walk_match:
                    walk_score = walk_match.group(1)
                    if 0 <= int(walk_score) <= 100:
                        property_data['walk_score'] = f"{walk_score}/100"
                        break
            
            bike_score_patterns = [
                r'Bike Score[®]?\s*(\d+)\s*/\s*100',
                r'Bike Score[®]?\s*(\d+)\s*\/\s*100',
                r'Bike Score[®]?[^0-9]*(\d+)',
            ]
            
            for pattern in bike_score_patterns:
                bike_match = re.search(pattern, page_text, re.I)
                if bike_match:
                    bike_score = bike_match.group(1)
                    if 0 <= int(bike_score) <= 100:
                        property_data['bike_score'] = f"{bike_score}/100"
                        break
            
            print("  - Neighborhood scores extraction completed")
            
        except Exception as e:
            print(f"  - Error in neighborhood scores extraction: {e}")
            property_data['walk_score'] = 'N/A'
            property_data['bike_score'] = 'N/A'
    
    def extract_schools_detailed(self, property_data):
        try:
            school_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'School') or contains(text(), 'school')]")
            if school_elements:
                self.driver.execute_script("arguments[0].scrollIntoView();", school_elements[0])
                time.sleep(2)
            
            school_types = {
                'elementary': ['elementary', 'primary', 'grade school'],
                'middle': ['middle', 'junior high', 'intermediate'],
                'high': ['high school', 'secondary', 'senior high']
            }
            
            for school_type, keywords in school_types.items():
                for keyword in keywords:
                    try:
                        school_elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
                        
                        for element in school_elements:
                            try:
                                container = element.find_element(By.XPATH, "./../..")
                                container_text = container.text
                                
                                lines = container_text.split('\n')
                                school_name = 'N/A'
                                for line in lines:
                                    if len(line) > 10 and not line.isdigit() and 'school' in line.lower():
                                        school_name = line.strip()
                                        break
                                
                                rating_match = re.search(r'(\d+)\s*(?:/\s*10|rating)', container_text, re.I)
                                school_rating = f"{rating_match.group(1)}/10" if rating_match else 'N/A'
                                
                                distance_match = re.search(r'(\d+\.\d+|\d+)\s*mi', container_text)
                                school_distance = distance_match.group(0) if distance_match else 'N/A'
                                
                                if school_name != 'N/A':
                                    property_data[f'{school_type}_school'] = {
                                        'name': school_name,
                                        'score': school_rating,
                                        'distance': school_distance
                                    }
                                    break
                                    
                            except:
                                continue
                        
                        if property_data[f'{school_type}_school']['name'] != 'N/A':
                            break
                            
                    except:
                        continue
            
        except Exception as e:
            pass
    
    def extract_environmental_risks(self, property_data):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            property_data['flood_risk'] = 'N/A'
            property_data['fire_risk'] = 'N/A'
            property_data['wind_risk'] = 'N/A'
            property_data['air_risk'] = 'N/A'
            property_data['heat_risk'] = 'N/A'
            
            try:
                climate_section = self.driver.find_element(By.XPATH, "//*[contains(text(), 'Climate risks')]")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", climate_section)
                time.sleep(3)
            except:
                pass
            
            risk_mappings = {
                'flood': 'flood_risk',
                'fire': 'fire_risk', 
                'wind': 'wind_risk',
                'air': 'air_risk',
                'heat': 'heat_risk'
            }
            
            for risk_type, risk_key in risk_mappings.items():
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{risk_type} factor')]")
                    
                    for element in elements:
                        try:
                            container = element.find_element(By.XPATH, "./../../..")
                            container_text = container.text
                            
                            level_match = re.search(r'(Minimal|Minor|Moderate|Major|Severe)', container_text, re.I)
                            score_match = re.search(r'(\d+)/10', container_text)
                            
                            if level_match and score_match:
                                level = level_match.group(1).title()
                                score = score_match.group(1)
                                property_data[risk_key] = f"{level} ({score}/10)"
                                break
                        except:
                            continue
                            
                    if property_data[risk_key] != 'N/A':
                        continue
                        
                except:
                    pass
                    
        except:
            pass
    
    def extract_market_data_detailed(self, property_data):
        try:
            history_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Price history') or contains(text(), 'Sold') or contains(text(), 'Listed')]")
            
            history = []
            for element in history_elements:
                try:
                    container = element.find_element(By.XPATH, "./..")
                    container_text = container.text
                    
                    history_matches = re.findall(r'(\d{1,2}/\d{1,2}/\d{4})\s+([A-Za-z\s]+)\s+(\$[\d,]+)', container_text)
                    for match in history_matches:
                        history.append({
                            'date': match[0],
                            'event': match[1].strip(),
                            'price': match[2]
                        })
                    
                    if len(history) >= 5:
                        break
                        
                except:
                    continue
            
            property_data['property_history'] = history
            
        except Exception as e:
            pass
    
    def extract_monthly_payment(self, property_data):
        try:
            payment_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Monthly') or contains(text(), 'monthly') or contains(text(), 'Payment')]")
            
            for element in payment_elements:
                try:
                    container = element.find_element(By.XPATH, "./..")
                    container_text = container.text
                    
                    payment_match = re.search(r'\$[\d,]+(?:/mo|/month|\s+monthly)', container_text, re.I)
                    if payment_match:
                        property_data['estimated_monthly_payment'] = payment_match.group(0)
                        break
                        
                except:
                    continue
            
            try:
                calc_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'mortgage') or contains(text(), 'calculator')]")
                for element in calc_elements:
                    parent = element.find_element(By.XPATH, "./..")
                    payment_match = re.search(r'\$[\d,]+', parent.text)
                    if payment_match and property_data['estimated_monthly_payment'] == 'N/A':
                        property_data['estimated_monthly_payment'] = payment_match.group(0)
                        break
            except:
                pass
                
        except Exception as e:
            pass
    
    def extract_nearby_cities(self, property_data):
        try:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            property_data['nearby_cities'] = []
            property_data['region'] = 'N/A'
            
            page_source = self.driver.page_source
            
            region_patterns = [
                r'Region:\s*([^<\n•]+)',
                r'Region[:\s]+([^<\n•]+)',
                r'Location[^<]*Region[:\s]*([^<\n•]+)'
            ]
            
            for pattern in region_patterns:
                region_match = re.search(pattern, page_source, re.I)
                if region_match:
                    region_text = region_match.group(1).strip()
                    if region_text and len(region_text) > 2:
                        property_data['region'] = region_text
                        break
            
            if property_data['region'] == 'N/A':
                try:
                    location_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Location')]")
                    for location_elem in location_elements:
                        try:
                            for xpath in [".//..", "./../..", "./../../../.."]:
                                container = location_elem.find_element(By.XPATH, xpath)
                                container_text = container.text
                                
                                region_match = re.search(r'Region:\s*([^•\n]+)', container_text, re.I)
                                if region_match:
                                    property_data['region'] = region_match.group(1).strip()
                                    break
                            
                            if property_data['region'] != 'N/A':
                                break
                        except:
                            continue
                except:
                    pass
            
            nearby_cities_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Nearby cities')]")
            
            if nearby_cities_elements:
                self.driver.execute_script("arguments[0].scrollIntoView();", nearby_cities_elements[0])
                time.sleep(2)
                
                container = nearby_cities_elements[0].find_element(By.XPATH, "./../..")
                city_links = container.find_elements(By.XPATH, ".//a[contains(text(), 'Real estate')]")
                
                cities = []
                for link in city_links[:5]:
                    try:
                        city_text = link.text.strip()
                        city_name = city_text.replace(' Real estate', '').strip()
                        if city_name and city_name not in cities:
                            cities.append(city_name)
                    except:
                        continue
                
                property_data['nearby_cities'] = cities
            
            if not property_data['nearby_cities']:
                nearby_section = re.search(r'Nearby cities(.*?)(?=<div|</section|</footer)', page_source, re.I | re.DOTALL)
                
                if nearby_section:
                    section_text = nearby_section.group(1)
                    city_matches = re.findall(r'([A-Za-z\s]+?)\s+Real estate', section_text)
                    
                    cities = []
                    for city in city_matches[:5]:
                        clean_city = city.strip()
                        if clean_city and len(clean_city) > 2:
                            cities.append(clean_city)
                    
                    property_data['nearby_cities'] = cities
                    
        except:
            pass
    
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
    print("MULTI-PROPERTY MASSACHUSETTS ZILLOW SCRAPER")
    print("="*80)
    
    # Get configuration from environment variables (for GitHub Actions) or use defaults
    max_properties = int(os.getenv('MAX_PROPERTIES', '10'))
    search_location = os.getenv('SEARCH_LOCATION', 'Boston-MA')
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    
    print(f"Configuration:")
    print(f"  • Max properties: {max_properties}")
    print(f"  • Search location: {search_location}")
    print(f"  • Headless mode: {headless}")
    print("="*80)
    
    # Build search URL with better logic
    if search_location.lower() in ['ma', 'massachusetts']:
        search_url = "https://www.zillow.com/homes/for_sale/Massachusetts_rb/"
    elif search_location.lower() in ['boston-ma', 'boston']:
        search_url = "https://www.zillow.com/boston-ma/"
    elif search_location.lower() in ['cambridge-ma', 'cambridge']:
        search_url = "https://www.zillow.com/cambridge-ma/"
    else:
        # For other locations, try the general format
        clean_location = search_location.replace('-', '-').lower()
        search_url = f"https://www.zillow.com/{clean_location}/"
    
    print(f"Search URL: {search_url}")
    
    # Initialize scraper with headless mode for GitHub Actions
    scraper = MultiPropertyZillowScraper(headless=headless)
    
    try:
        print(f"\nTesting navigation to search page...")
        
        # Navigate to search page first and debug
        scraper.driver.get(search_url)
        time.sleep(10)  # Wait longer for page load
        
        print(f"Current URL after navigation: {scraper.driver.current_url}")
        print(f"Page title: {scraper.driver.title}")
        
        # Try to find search results with multiple selectors
        search_selectors = [
            '//*[@id="grid-search-results"]/ul',
            '//*[@id="grid-search-results"]',
            '//ul[contains(@class, "photo-cards")]',
            '//div[contains(@class, "search-page-react-content")]',
            '//article[contains(@class, "property-card")]',
            '//div[contains(@class, "PropertyCardWrapper")]',
            '//a[contains(@href, "/homedetails/")]'
        ]
        
        results_found = False
        for i, selector in enumerate(search_selectors):
            try:
                elements = scraper.driver.find_elements(By.XPATH, selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements with selector {i+1}: {selector}")
                    results_found = True
                    break
                else:
                    print(f"✗ No elements found with selector {i+1}: {selector}")
            except Exception as e:
                print(f"✗ Error with selector {i+1}: {e}")
        
        if not results_found:
            print("\n❌ No search results found with any selector")
            print("Saving page source for debugging...")
            
            # Save page source for debugging
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(scraper.driver.page_source)
            print("✓ Page source saved to debug_page.html")
            
            # Also save a screenshot if possible
            try:
                scraper.driver.save_screenshot("debug_screenshot.png")
                print("✓ Screenshot saved to debug_screenshot.png")
            except:
                print("✗ Could not save screenshot")
        else:
            print("✓ Search results found! Starting scraping...")
            # Scrape properties
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
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            scraper.driver.quit()
        except:
            pass
    
    print("\n" + "="*80)
    print("SCRAPING SESSION ENDED")
    print("="*80)
