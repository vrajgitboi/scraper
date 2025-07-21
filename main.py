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

if __name__ == "__main__":

    print("="*80)
    print("QUEUE-BASED MASSACHUSETTS ZILLOW SCRAPER - 10,000 PROPERTIES TARGET")
    print("="*80)

    # --- MODIFICATION START ---
    # Get terminal/queue ID from environment variable (1-8)
    # The original line is commented out and replaced to always run queue 2.
    # queue_id = int(os.getenv('QUEUE_ID', '1'))
    queue_id = 2  # Directly runs the 2nd queue
    # --- MODIFICATION END ---
    
    headless = os.getenv('HEADLESS', 'false').lower() == 'true'
    output_base_dir = os.getenv('OUTPUT_DIR', 'data')

    # Get the queue for this terminal
    my_queue = city_queues.get(queue_id, city_queues[1])

    # Calculate expected total for this queue
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

    # Create base output directory - FIX 2: Use absolute paths
    base_dir = os.path.abspath(output_base_dir)
    os.makedirs(base_dir, exist_ok=True)

    # Initialize scraper once for all cities
    try:
        scraper = MultiPropertyZillowScraper(headless=headless)
    except Exception as e:
        print(f"❌ Failed to initialize scraper: {e}")
        exit(1)

    # Process each city in the queue
    total_properties_scraped = 0
    cities_completed = 0
    cities_failed = 0

    for city_index, (city, max_properties_this_city, search_url) in enumerate(my_queue, 1):
        print(f"\n" + "🏙️ " * 20)
        print(f"QUEUE {queue_id} - CITY {city_index}/{len(my_queue)}: {city}")
        print(f"Target: {max_properties_this_city} properties")
        print(f"Using optimized search URL: {search_url[:60]}...")
        print(f"🏙️ " * 20)

        try:
            # FIX 3: Create city-specific output directory with absolute paths
            city_dir_name = city.replace('-ma', '').replace('-', '_').lower()
            city_output_dir = os.path.join(base_dir, f"queue_{queue_id}", city_dir_name)
            os.makedirs(city_output_dir, exist_ok=True)

            # FIX 4: Don't change directories - use absolute paths
            print(f"📁 Output directory: {city_output_dir}")

            # Scrape properties for this city
            print(f"\n🚀 Starting to scrape {max_properties_this_city} properties from {city}...")
            all_properties = scraper.scrape_multiple_properties
