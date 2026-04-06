from curl_cffi import requests
import feedparser
import argparse
from lxml import etree
import time
import json
import os
from bs4 import BeautifulSoup
import trafilatura

CACHE_FILE = 'cache.json'

NATIONAL_PUBLISHERS = {
    'ABC News', 'AP News', 'Al Jazeera', 'BBC', 'CNBC', 'CNN', 
    'NASA (.gov)', 'NASA Science (.gov)', 'NBC News', 'NPR', 
    'National Geographic', 'PBS', 'Reuters', 'Scientific American', 'Space', 
    'The Guardian', 'The New York Times', 'The Washington Post', 'USA Today', 
    'The Verge', 'Wired', 'Ars Technica', 'Axios', 'Bloomberg', 
    'Wall Street Journal', 'The Atlantic', 'Forbes', 'Time', 'cbsnews.com',
    'cbc.ca', 'CTV News', 'Financial Times', 'The New Yorker', 'Vox', 'The Hill',
    'Politico', 'Popular Science', 'Live Science', 'The Economist', 'HuffPost', 
    'Business Insider', 'Mashable', 'The Independent', 'The Boston Globe', 
    'The Seattle Times', 'The Daily Beast', 'New York Post', 'CBS News', 
    'Associated Press', 'Nature'
}

def is_national_publisher(entry):
    """Checks if the entry is from a larger national publication."""
    source = entry.get('source', {}).get('title', '').strip()
    if not source:
        # Try to extract from title "Title - Source"
        if ' - ' in entry.title:
            source = entry.title.split(' - ')[-1].strip()
    
    if not source:
        return False
    
    source_lower = source.lower()
    whitelist_lower = {p.lower() for p in NATIONAL_PUBLISHERS}
    
    # Direct match or any whitelist item contained in the source title
    if source_lower in whitelist_lower:
        return True
    
    for pub in whitelist_lower:
        if pub in source_lower:
            return True
            
    return False

def clean_extracted_content(html_content):
    """Post-processes extracted HTML to remove remaining ad or navigation text."""
    if not html_content:
        return None
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Patterns to remove (case-insensitive)
    bad_patterns = [
        "video ad feedback",
        "video ad",
        "advertisement",
        "sign up for our newsletter",
        "subscribe to",
        "read more:",
        "related stories",
        "click here",
        "supported by",
        "follow us on",
        "share this",
        "loading...",
        "please enable javascript",
        "your browser does not support",
        "all rights reserved",
        "copyright",
        "here’s what else you need to know",
        "get up to speed and on with your day",
        "shopping trends team",
        "independent of the journalists",
        "may earn a commission",
        "subscribe to our",
        "read the full story",
    ]
    
    for element in soup.find_all(['p', 'div', 'span', 'h4', 'h5', 'h6', 'strong']):
        text = element.get_text().strip().lower()
        if not text:
            continue
        if any(p in text for p in bad_patterns):
            # If it's a small element or specifically matches a pattern, remove it
            if len(text) < 200: # Don't remove huge paragraphs by accident
                element.decompose()
            
    # Remove empty elements
    for element in soup.find_all():
        if len(element.get_text(strip=True)) == 0 and element.name not in ['img', 'graphic']:
            element.decompose()
            
    return str(soup)

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    return {}

def save_cache(cache):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def resolve_google_url(google_url):
    """
    Resolves a Google News redirect URL to its final destination using the 2024/2025 batchexecute method.
    """
    try:
        # Use curl_cffi for resolving too, to be safe
        response = requests.get(google_url, impersonate="chrome", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Extract the 'data-p' attribute from c-wiz
        wiz_element = soup.select_one('c-wiz[data-p]')
        if not wiz_element:
            return response.url
            
        data_p = wiz_element.get('data-p')
        
        # 3. Format the payload for the batchexecute API
        obj = json.loads(data_p.replace('%.@.', '["garturlreq",'))
        payload = {
            'f.req': json.dumps([[['Fbv4je', json.dumps(obj[:-6] + obj[-2:]), 'null', 'generic']]])
        }
        
        # 4. Send the POST request to the decoder endpoint
        api_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
        post_resp = requests.post(api_url, impersonate="chrome", data=payload, timeout=10)
        
        # 5. Parse the response
        cleaned_response = post_resp.text.replace(")]}'", "").strip()
        response_data = json.loads(cleaned_response)
        
        # The final URL is nested deep in the response array
        article_url = json.loads(response_data[0][2])[1]
        return article_url
        
    except Exception as e:
        print(f"Error resolving {google_url}: {e}")
        return google_url

def extract_content(url):
    """Extracts the full text and lead image of an article using curl_cffi for Cloudflare bypass."""
    try:
        # impersonate="chrome" mimics a real browser TLS fingerprint
        response = requests.get(url, impersonate="chrome", timeout=20)
        if response.status_code == 200:
            html = response.text
            # Extract HTML content with formatting and images
            # include_links=False helps remove a lot of navigation text
            content = trafilatura.extract(html, include_images=True, include_formatting=True, 
                                          output_format='html', favor_precision=True,
                                          include_links=False)
            
            # Post-process to remove remaining junk
            content = clean_extracted_content(content)
            
            # Try to get a lead image from metadata
            metadata = trafilatura.extract_metadata(html)
            lead_image = getattr(metadata, 'image', None) if metadata else None
            
            return content, lead_image
        else:
            print(f"Failed to fetch {url}, status: {response.status_code}")
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
    return None, None

def main(searches, use_cache=True):
    cache = load_cache() if use_cache else {}

    for search in searches:
        name = search.get('name', 'Unknown')
        feed_url = search.get('url')
        output_file = search.get('output', 'resolved_news.xml')
        
        if not feed_url:
            print(f"Skipping search '{name}' due to missing URL.")
            continue

        print(f"\n--- Processing search: {name} ---")
        print(f"Fetching feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        # Create the root element for the new XML
        root = etree.Element("rss", version="2.0")
        channel = etree.SubElement(root, "channel")
        
        # Copy channel-level info
        title = etree.SubElement(channel, "title")
        title.text = feed.channel.get('title', f"Google News Resolved - {name}")
        
        link = etree.SubElement(channel, "link")
        link.text = feed.channel.get('link', '')
        
        description = etree.SubElement(channel, "description")
        description.text = feed.channel.get('description', f"Resolved Google News RSS feed for {name} with full text")

        # Filter for national publishers
        all_entries = feed.entries
        national_entries = [e for e in all_entries if is_national_publisher(e)]
        print(f"Found {len(national_entries)} national entries out of {len(all_entries)} total.")

        # Limit to the most recent 25 national entries
        entries_to_process = national_entries[:25]
        print(f"Processing {len(entries_to_process)} national entries (limited to 25)...")
        for entry in entries_to_process:
            # Check cache
            cache_entry = cache.get(entry.link)
            if cache_entry and isinstance(cache_entry, dict) and cache_entry.get('content'):
                resolved_link = cache_entry.get('url')
                full_text = cache_entry.get('content')
                lead_image = cache_entry.get('lead_image')
                print(f"Cache hit: {entry.link}")
            else:
                print(f"Resolving: {entry.link}")
                resolved_link = resolve_google_url(entry.link)
                print(f"Resolved to: {resolved_link}")
                
                # Extract content
                full_text, lead_image = extract_content(resolved_link)
                
                if full_text:
                    # Update cache
                    cache[entry.link] = {
                        'url': resolved_link,
                        'content': full_text,
                        'lead_image': lead_image,
                        'timestamp': time.time()
                    }
                
                # Wait to avoid being rate-limited
                time.sleep(1.0)

            # Skip this entry if we couldn't get the full text or resolution failed
            if not full_text:
                print(f"Skipping {entry.link} due to missing content or resolution error.")
                continue

            item = etree.SubElement(channel, "item")
            
            # Original Title
            item_title = etree.SubElement(item, "title")
            item_title.text = entry.title
            
            # Original PubDate
            item_pubdate = etree.SubElement(item, "pubDate")
            item_pubdate.text = entry.get('published', '')
            
            # Item Link
            item_link = etree.SubElement(item, "link")
            item_link.text = resolved_link
            
            # Description (using full text if available)
            # Prepend lead image if available
            final_description = ""
            if lead_image:
                final_description += f'<img src="{lead_image}" style="max-width: 100%; height: auto; display: block; margin-bottom: 1em;" />'
            
            final_description += full_text

            item_desc = etree.SubElement(item, "description")
            # Use CDATA for HTML content
            item_desc.text = etree.CDATA(final_description)
            
            # Source
            if 'source' in entry:
                source = etree.SubElement(item, "source", url=entry.source.get('href', ''))
                source.text = entry.source.get('title', '')
                
            # Guid
            item_guid = etree.SubElement(item, "guid", isPermaLink="false")
            item_guid.text = entry.get('id', resolved_link)

        # Write to file for EACH search
        xml_data = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="utf-8")
        with open(output_file, "wb") as f:
            f.write(xml_data)
        print(f"Saved resolved feed to {output_file}")

    # Save cache once at the end
    save_cache(cache)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Google News RSS redirects and extract content.")
    parser.add_argument("--config", default="searches.json", help="Path to JSON configuration file with searches")
    parser.add_argument("--no-cache", action="store_true", help="Ignore any cached content and regenerate fresh")
    
    args = parser.parse_args()
    
    if os.path.exists(args.config):
        try:
            with open(args.config, 'r') as f:
                searches_to_run = json.load(f)
        except Exception as e:
            print(f"Error reading config {args.config}: {e}")
            exit(1)
    else:
        # Fallback to single default search if config doesn't exist
        searches_to_run = [{
            "name": "Artemis II",
            "url": "https://news.google.com/rss/search?q=Artemis+II&hl=en-US&gl=US&ceid=US:en",
            "output": "resolved_news.xml"
        }]
        
    main(searches_to_run, use_cache=not args.no_cache)
