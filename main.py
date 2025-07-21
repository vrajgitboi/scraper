import time
import json
import random
from datetime import datetime
from city_queues import city_queues, get_queue_summary
import os
from zillow import MultiPropertyZillowScraper

def smart_sleep(sleep_type):
    """Smart randomized delays"""
    sleep_ranges = {
        'between_properties': (1.5, 3.0),
        'between_cities': (45, 75),        # Randomized city breaks
        'after_error': (10, 20),           # Error recovery
        'navigation': (2, 4)               # General navigation
    }
    delay = random.uniform(*sleep_ranges.get(sleep_type, (2, 4)))
    return delay

# All the executable code MUST be inside this block
if __name__ == "__main__":

    print("="*80)
    print("QUEUE-BASED MASSACHUSETTS ZILLOW SCRAPER - 10,000 PROPERTIES TARGET")
    print("="*80)

    # Hardcode the queue_id to 2
    queue_id = 2
    
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    output_base_dir = os.getenv('OUTPUT_DIR', 'data')

    # This is where 'my_queue' gets defined. It must happen before the loop.
    my_queue = city_queues.get(queue_id, city_queues[1])

    expected_total = sum(count for city, count, _ in my_queue)

    print(f"Configuration:")
    print(f"  • Queue ID: {queue_id}")
    print(f"  • Cities in queue: {len(my_queue)}")
    print(f"  • Expected properties: {expected_total}")
    print(f"  • Headless mode: {headless}")
    print(f"  • Output base directory: {output_base_dir}")
    print("-" * 60)
    print(f"Queue {queue_id} cities:")
    for city, count, _ in my_queue:
        print(f"  • {city}: {count} properties")
    print("="*80)

    base_dir = os.path.abspath(output_base_dir)
    os.makedirs(base_dir, exist_ok=True)

    try:
        scraper = MultiPropertyZillowScraper(headless=headless)
        
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {e}")
        exit(1)

    total_properties_scraped = 0
    cities_completed = 0
    cities_failed = 0

    # This for loop is now correctly indented inside the if block
    for city_index, (city, max_properties_this_city, search_url) in enumerate(my_queue, 1):
        print(f"\n" + "🏙️ " * 20)
        print(f"QUEUE {queue_id} - CITY {city_index}/{len(my_queue)}: {city}")
        print(f"Target: {max_properties_this_city} properties")
        print(f"Using optimized search URL: {search_url[:60]}...")
        print(f"🏙️ " * 20)
        
        city_output_dir = "" # Initialize to avoid reference before assignment in except block
        try:
            city_dir_name = city.replace('-ma', '').replace('-', '_').lower()
            city_output_dir = os.path.join(base_dir, f"queue_{queue_id}", city_dir_name)
            os.makedirs(city_output_dir, exist_ok=True)
            
            print(f"📁 Output directory: {city_output_dir}")

            print(f"\n🚀 Starting to scrape {max_properties_this_city} properties from {city}...")
            all_properties = scraper.scrape_multiple_properties(search_url, max_properties=max_properties_this_city)

            if all_properties:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_city_name = city.replace('-ma', '').replace('-', '_').lower()
                filename_prefix = f"zillow_q{queue_id}_{safe_city_name}_{max_properties_this_city}props_{timestamp}"

                original_cwd = os.getcwd()
                try:
                    os.chdir(city_output_dir)
                    json_file, csv_file = scraper.save_all_properties(filename_prefix=filename_prefix)
                finally:
                    os.chdir(original_cwd)

                city_summary = {
                    "queue_id": queue_id, "city": city, "target_properties": max_properties_this_city,
                    "actual_properties": len(all_properties), "city_index": city_index, "timestamp": timestamp,
                    "json_file": json_file, "csv_file": csv_file, "output_directory": city_output_dir,
                    "success_rate": (len(all_properties) / max_properties_this_city) * 100
                }

                summary_file = os.path.join(city_output_dir, f"summary_q{queue_id}_{safe_city_name}_{timestamp}.json")
                with open(summary_file, 'w') as f:
                    json.dump(city_summary, f, indent=2)

                print(f"\n✅ {city} COMPLETED! Target: {max_properties_this_city}, Actual: {len(all_properties)}")
                
                total_properties_scraped += len(all_properties)
                cities_completed += 1
                
                scraper.all_properties_data = []
                scraper.scraped_urls = set()
                
            else:
                print(f"\n❌ {city} FAILED - No properties scraped")
                cities_failed += 1
                
        except Exception as e:
            print(f"\n❌ ERROR in {city}: {e}")
            import traceback
            traceback.print_exc()
            cities_failed += 1
            
            if hasattr(scraper, 'all_properties_data') and scraper.all_properties_data:
                try:
                    if city_output_dir:
                        original_cwd = os.getcwd()
                        os.chdir(city_output_dir)
                        scraper.save_all_properties(filename_prefix=f"zillow_{city}_error_partial")
                        os.chdir(original_cwd)
                    scraper.all_properties_data = []
                except Exception as save_error:
                    print(f"⚠️ Could not save partial data: {save_error}")
            
            time.sleep(smart_sleep('after_error'))
        
        remaining_cities = len(my_queue) - city_index
        print(f"\n📊 QUEUE {queue_id} PROGRESS: {cities_completed}/{len(my_queue)} cities done. {remaining_cities} remaining.")
        
        if remaining_cities > 0:
            time.sleep(smart_sleep('between_cities'))
    
    try:
        scraper.driver.quit()
        print("🔧 Browser closed successfully")
    except Exception as e:
        print(f"⚠️ Browser cleanup warning: {e}")
    
    print(f"\n🎉 QUEUE {queue_id} COMPLETED! Total properties scraped: {total_properties_scraped}/{expected_total}")
