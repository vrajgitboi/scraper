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
        self.setup_driver(headless)
        
    def setup_driver(self, headless):
        try:
            import undetected_chromedriver as uc
            
            options = uc.ChromeOptions()
            if headless:
                options.add_argument("--headless=new")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")
            
            self.driver = uc.Chrome(options=options, version_main=None)
            
        except Exception as e:
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            if headless:
                options.add_argument("--headless")
            
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
    
    def scrape_multiple_properties(self, property_urls, max_properties=None):
        """Scrape multiple properties from provided URLs list"""
        if max_properties is None:
            max_properties = len(property_urls)
        
        print(f"Starting to scrape {min(max_properties, len(property_urls))} properties from provided URLs...")
        
        properties_scraped = 0
        
        for i, url in enumerate(property_urls):
            if properties_scraped >= max_properties:
                break
                
            try:
                print(f"\nProcessing property {properties_scraped + 1}/{max_properties}")
                print(f"URL: {url}")
                
                # Navigate directly to the property page
                self.driver.get(url)
                time.sleep(random.uniform(3, 5))
                
                # Extract property data
                property_data = self.extract_complete_property_data()
                
                if property_data:
                    self.all_properties_data.append(property_data)
                    properties_scraped += 1
                    print(f"✓ Successfully scraped property {properties_scraped}")
                else:
                    print("✗ Failed to extract property data")
                
                # Wait before processing next property
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"✗ Error processing property {i+1}: {e}")
                continue
        
        print(f"\n🎉 Completed! Scraped {len(self.all_properties_data)} properties total.")
        return self.all_properties_data
    
    def extract_complete_property_data(self):
        """Extract all property data from current property page"""
        try:
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
            
            self.extract_price_and_basic_info(property_data)
            self.extract_property_features_detailed(property_data)
            self.extract_neighborhood_scores_detailed(property_data)
            self.extract_schools_detailed(property_data)
            self.extract_environmental_risks(property_data)
            self.extract_market_data_detailed(property_data)
            self.extract_monthly_payment(property_data)
            self.extract_nearby_cities(property_data)
            
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
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        
        try:
            expandable_buttons = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'See more') or contains(text(), 'Show more') or contains(text(), 'Facts')]")
            for button in expandable_buttons:
                try:
                    self.driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)
                except:
                    pass
        except:
            pass
        
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
    
    def extract_neighborhood_scores_detailed(self, property_data):
        try:
            getting_around_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Getting around')]")
            if getting_around_elements:
                self.driver.execute_script("arguments[0].scrollIntoView();", getting_around_elements[0])
                time.sleep(3)
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
            time.sleep(3)
            
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
            time.sleep(3)
            
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
    
    def save_all_properties(self, filename_prefix="specific_properties"):
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
    print("="*80)
    print("MULTI-PROPERTY MASSACHUSETTS ZILLOW SCRAPER")
    print("Scraping specific property URLs...")
    print("="*80)
    
    # Your specific property URLs
    property_urls = [
        "https://www.zillow.com/homedetails/29-Sunset-Dr-Seekonk-MA-02771/56873494_zpid/",
        "https://www.zillow.com/homedetails/20-Thomas-Coles-Ln-Wellfleet-MA-02667/56792531_zpid/",
        "https://www.zillow.com/homedetails/27-Keans-Rd-Burlington-MA-01803/57055935_zpid/",
        "https://www.zillow.com/homedetails/14-Evelyn-Way-Seekonk-MA-02771/119100960_zpid/",
        "https://www.zillow.com/homedetails/31-John-Joseph-Rd-Harwich-MA-02645/186990206_zpid/",
        "https://www.zillow.com/homedetails/23-Hickory-Ridge-Rd-Rehoboth-MA-02769/56867985_zpid/",
        "https://www.zillow.com/homedetails/10-Maple-St-Wenham-MA-01984/56971836_zpid/",
        "https://www.zillow.com/homedetails/329-Lakeshore-Dr-Sandisfield-MA-01255/56814450_zpid/",
        "https://www.zillow.com/homedetails/111-Autran-Ave-North-Andover-MA-01845/56097558_zpid/"
    ]
    
    # Initialize scraper
    scraper = MultiPropertyZillowScraper(headless=False)
    
    try:
        # Scrape multiple properties from the URL list
        all_properties = scraper.scrape_multiple_properties(property_urls, max_properties=len(property_urls))
        
        # Save all data
        if all_properties:
            json_file, csv_file = scraper.save_all_properties()
            
            # Print summary
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
            scraper.save_all_properties(filename_prefix="specific_properties_partial")
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        if scraper.all_properties_data:
            print("Saving partial data...")
            scraper.save_all_properties(filename_prefix="specific_properties_error")
    
    finally:
        # Clean up
        try:
            scraper.driver.quit()
        except:
            pass
    
    print("\n" + "="*80)
    print("SCRAPING SESSION ENDED")
    print("="*80)
