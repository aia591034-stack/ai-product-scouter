from playwright.sync_api import sync_playwright
import time
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def scrape_mercari(keyword):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True) # Headless=True for speed now
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = context.new_page()

        # Build URL
        url = f"https://jp.mercari.com/search?keyword={keyword}"
        print(f"Navigating to: {url}")
        
        try:
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000) 
            
            items = page.locator('li[data-testid="item-cell"]')
            count = items.count()
            print(f"Found {count} items.")

            if count > 0:
                print("--- DEBUG: HTML of first item ---")
                first_item_html = items.first.inner_html()
                print(first_item_html[:500]) # Print first 500 chars to check structure
                print("---------------------------------")

            for i in range(min(count, 5)):
                item = items.nth(i)
                try:
                    # Title (from image alt seems okay, just need to clean it)
                    img = item.locator('img').first
                    title = img.get_attribute('alt') if img.count() > 0 else "No Title"
                    
                    # Price - Attempt to find by text content if class fails
                    price_element = item.locator('span').filter(has_text="¥")
                    if price_element.count() > 0:
                        price = price_element.first.inner_text()
                    else:
                        # Fallback: finding any number that looks like a price
                        price = "N/A"
                        # Try finding element with aria-label="price" or similar if it exists
                        # (Checking debug output will help confirm this)

                    print(f"Item {i+1}: {title} - {price}")
                except Exception as e:
                    print(f"Error extracting item {i+1}: {e}")

        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    scrape_mercari("macbook")
