import feedparser
import requests
import argparse
from lxml import etree
import time

def resolve_url(url):
    """Resolves a Google News redirect URL to its final destination."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }
        # Use GET instead of HEAD because many news sites block HEAD requests
        # We only need the final URL, so we can use stream=True to avoid downloading the whole body
        with requests.get(url, allow_redirects=True, headers=headers, timeout=15, stream=True) as response:
            return response.url
    except Exception as e:
        print(f"Error resolving {url}: {e}")
        return url

def main(feed_url, output_file):
    print(f"Fetching feed: {feed_url}")
    feed = feedparser.parse(feed_url)
    
    # Create the root element for the new XML
    root = etree.Element("rss", version="2.0")
    channel = etree.SubElement(root, "channel")
    
    # Copy channel-level info
    title = etree.SubElement(channel, "title")
    title.text = feed.channel.get('title', 'Google News Resolved')
    
    link = etree.SubElement(channel, "link")
    link.text = feed.channel.get('link', '')
    
    description = etree.SubElement(channel, "description")
    description.text = feed.channel.get('description', 'Resolved Google News RSS feed')

    print(f"Processing {len(feed.entries)} entries...")
    for entry in feed.entries:
        item = etree.SubElement(channel, "item")
        
        # Original Title
        item_title = etree.SubElement(item, "title")
        item_title.text = entry.title
        
        # Original PubDate
        item_pubdate = etree.SubElement(item, "pubDate")
        item_pubdate.text = entry.get('published', '')
        
        # Resolved Link
        print(f"Resolving: {entry.link}")
        resolved_link = resolve_url(entry.link)
        item_link = etree.SubElement(item, "link")
        item_link.text = resolved_link
        
        # Description
        item_desc = etree.SubElement(item, "description")
        item_desc.text = entry.get('summary', '')
        
        # Source
        if 'source' in entry:
            source = etree.SubElement(item, "source", url=entry.source.get('href', ''))
            source.text = entry.source.get('title', '')
            
        # Guid
        item_guid = etree.SubElement(item, "guid", isPermaLink="false")
        item_guid.text = entry.get('id', resolved_link)
        
        # Wait to avoid being rate-limited by destination servers
        time.sleep(0.5)

    # Write to file
    tree = etree.ElementTree(root)
    tree.write(output_file, pretty_print=True, xml_declaration=True, encoding="utf-8")
    print(f"Saved resolved feed to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resolve Google News RSS redirects.")
    parser.add_argument("--url", default="https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en", help="Google News RSS URL")
    parser.add_argument("--output", default="resolved_news.xml", help="Output XML filename")
    
    args = parser.parse_args()
    main(args.url, args.output)
