import requests
from bs4 import BeautifulSoup
import json
import trafilatura

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
        print(f"Status Code: {response.status_code}")
        html = response.text
        if response.status_code == 200:
            # Extract HTML content with formatting and images
            content = trafilatura.extract(html, include_images=True, include_formatting=True, output_format='html')
            
            # Try to get a lead image from metadata
            metadata = trafilatura.extract_metadata(html)
            lead_image = getattr(metadata, 'image', None) if metadata else None
            
            return content, lead_image, html
        else:
            return None, None, html
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
    return None, None, None

test_url = "https://news.google.com/rss/articles/CBMinAFBVV95cUxNRGVxeHBHQlJaV0tKa2RJTDdkbExXNnBGX1pLallTX3B5dUlkYk9OWmtVV1M1MnNLZ2c3dFFtc1pudHJNYmJ2YmQ4cjJ3T3lnUFpwN2lxWVlpaDI1VDNyU3FnUnROQWdkbUxBRktKM1EwNXlWdHRWa0c0eEsybzVUZFIwakdJOXRGVGFGcXhqWFlCWnZYRWFUTjRwaGc?oc=5"
print(f"Testing URL: {test_url}")
resolved_url = resolve_google_url(test_url)
print(f"Resolved URL: {resolved_url}")
content, lead_image, raw_html = extract_content(resolved_url)

if content:
    print("--- CONTENT ---")
    print(content[:500])
else:
    print("No content extracted!")
    print(f"RAW HTML (Type: {type(raw_html)}):")
    print(f"'{raw_html}'")
