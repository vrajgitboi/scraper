# --- In main.py, REPLACE the entire 'for' loop with this block ---

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

    # This 'try' block must have a corresponding 'except' block.
    try:
        city_dir_name = city.replace('-ma', '').replace('-', '_').lower()
        city_output_dir = os.path.join(base_dir, f"queue_{queue_id}", city_dir_name)
        os.makedirs(city_output_dir, exist_ok=True)
        
        print(f"📁 Output directory: {city_output_dir}")

        # Scrape properties for this city
        print(f"\n🚀 Starting to scrape {max_properties_this_city} properties from {city}...")
        all_properties = scraper.scrape_multiple_properties(search_url, max_properties=max_properties_this_city)

        # Save data for this city with unique naming
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

            # Create city summary
            city_summary = {
                "queue_id": queue_id,
                "city": city,
                "target_properties": max_properties_this_city,
                "actual_properties": len(all_properties),
                "city_index": city_index,
                "timestamp": timestamp,
                "json_file": json_file,
                "csv_file": csv_file,
                "output_directory": city_output_dir,
                "success_rate": (len(all_properties) / max_properties_this_city) * 100
            }

            summary_file = os.path.join(city_output_dir, f"summary_q{queue_id}_{safe_city_name}_{timestamp}.json")
            with open(summary_file, 'w') as f:
                json.dump(city_summary, f, indent=2)

            print(f"\n✅ {city} COMPLETED!")
            print(f"   🎯 Target: {max_properties_this_city} properties")
            print(f"   ✓ Actual: {len(all_properties)} properties")
            print(f"   📈 Success: {(len(all_properties)/max_properties_this_city)*100:.1f}%")
            print(f"   📁 Data saved to: {city_output_dir}")
            print(f"   📄 Files: {json_file}, {csv_file}")
            
            total_properties_scraped += len(all_properties)
            cities_completed += 1
            
            # Clear the scraper's data for next city
            scraper.all_properties_data = []
            scraper.scraped_urls = set()
            
        else:
            print(f"\n❌ {city} FAILED - No properties scraped")
            cities_failed += 1
            
    # --- THIS IS THE CRITICAL BLOCK THAT WAS LIKELY MISSING ---
    except Exception as e:
        print(f"\n❌ FATAL ERROR in {city}: {e}")
        import traceback
        traceback.print_exc()
        cities_failed += 1
        
        # Try to save partial data if any
        if hasattr(scraper, 'all_properties_data') and scraper.all_properties_data:
            try:
                # Ensure city_output_dir is defined before trying to use it
                if 'city_output_dir' in locals():
                    original_cwd = os.getcwd()
                    os.chdir(city_output_dir)
                    scraper.save_all_properties(filename_prefix=f"zillow_{city}_error_partial")
                    os.chdir(original_cwd)
                scraper.all_properties_data = []
            except Exception as save_error:
                print(f"⚠️ Could not save partial data: {save_error}")
        
        # Longer delay after errors
        error_delay = smart_sleep('after_error')
        print(f"⏳ Error recovery delay: {error_delay:.1f} seconds...")
        time.sleep(error_delay)
    
    # Progress update
    remaining_cities = len(my_queue) - city_index
    progress_percentage = (total_properties_scraped / expected_total) * 100 if expected_total > 0 else 0
    
    print(f"\n📊 QUEUE {queue_id} PROGRESS:")
    print(f"   • Completed: {cities_completed}/{len(my_queue)} cities")
    print(f"   • Failed: {cities_failed}/{len(my_queue)} cities")
    print(f"   • Remaining: {remaining_cities} cities")
    print(f"   • Total properties: {total_properties_scraped}/{expected_total} ({progress_percentage:.1f}%)")
    
    # Smart randomized delays between cities
    if remaining_cities > 0:
        next_city, next_target, _ = my_queue[city_index]
        print(f"   • Next city: {next_city} (target: {next_target} properties)")
        
        city_delay = smart_sleep('between_cities')
        print(f"\n⏳ City break: {city_delay:.1f} seconds before {next_city}...")
        time.sleep(city_delay)
