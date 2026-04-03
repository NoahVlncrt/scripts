import feedparser
import requests
import argparse
from lxml import etree
import time
import json
import os
from bs4 import BeautifulSoup
import trafilatura

CACHE_FILE = 'cache.json'

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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        # 1. Fetch the intermediate page
        response = requests.get(google_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Extract the 'data-p' attribute from c-wiz
        wiz_element = soup.select_one('c-wiz[data-p]')
        if not wiz_element:
            # Fallback to simple response.url if we can't find the token
            return response.url
            
        data_p = wiz_element.get('data-p')
        
        # 3. Format the payload for the batchexecute API
        obj = json.loads(data_p.replace('%.@.', '["garturlreq",'))
        payload = {
            'f.req': json.dumps([[['Fbv4je', json.dumps(obj[:-6] + obj[-2:]), 'null', 'generic']]])
        }
        
        # 4. Send the POST request to the decoder endpoint
        api_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
        post_resp = requests.post(api_url, headers=headers, data=payload, timeout=10)
        
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
    """Extracts the full text and lead image of an article."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            html = response.text
            # Extract HTML content with formatting and images
            content = trafilatura.extract(html, include_images=True, include_formatting=True, output_format='html')
            
            # Try to get a lead image from metadata
            metadata = trafilatura.extract_metadata(html)
            lead_image = getattr(metadata, 'image', None) if metadata else None
            
            return content, lead_image
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
    return None, None

def main(feed_url, output_file):
    print(f"Fetching feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    
    cache = load_cache()

    # Create the root element for the new XML
    root = etree.Element("rss", version="2.0")
    channel = etree.SubElement(root, "channel")
    
    # Copy channel-level info
    title = etree.SubElement(channel, "title")
    title.text = feed.channel.get('title', 'Google News Resolved')
    
    link = etree.SubElement(channel, "link")
    link.text = feed.channel.get('link', '')
    
    description = etree.SubElement(channel, "description")
    description.text = feed.channel.get('description', 'Resolved Google News RSS feed with full text')

    print(f"Processing {len(feed.entries)} entries...")
    for entry in feed.entries:
        item = etree.SubElement(channel, "item")
        
        # Original Title
        item_title = etree.SubElement(item, "title")
        item_title.text = entry.title
        
        # Original PubDate
        item_pubdate = etree.SubElement(item, "pubDate")
        item_pubdate.text = entry.get('published', '')
        
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
            
            # Extract content if we have a new URL
            full_text, lead_image = extract_content(resolved_link)
            
            # Update cache with URL, content, and lead image
            cache[entry.link] = {
                'url': resolved_link,
                'content': full_text,
                'lead_image': lead_image,
                'timestamp': time.time()
            }
            
            # Wait to avoid being rate-limited
            time.sleep(1.0)
        
        # Item Link
        item_link = etree.SubElement(item, "link")
        item_link.text = resolved_link
        
        # Description (using full text if available, otherwise original summary)
        # Prepend lead image if available
        final_description = ""
        if lead_image:
            final_description += f'<img src="{lead_image}" style="max-width: 100%; height: auto; display: block; margin-bottom: 1em;" />'
        
        if full_text:
            final_description += full_text
        else:
            final_description += entry.get('summary', '')

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

    save_cache(cache)

    # Write to file
    tree = etree.ElementTree(root)
    tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"Saved resolved feed to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Google News RSS redirects and extract content.")
    parser.add_argument("--url", default="https://news.google.com/rss/search?q=Artemis+II&hl=en-US&gl=US&ceid=US:en", help="Google News RSS URL")
    parser.add_argument("--output", default="resolved_news.xml", help="Output XML filename")
    
    args = parser.parse_args()
    main(args.url, args.output)
