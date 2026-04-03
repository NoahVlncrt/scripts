import trafilatura
import json
import requests
from bs4 import BeautifulSoup

def resolve_google_url(google_url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        response = requests.get(google_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        wiz_element = soup.select_one('c-wiz[data-p]')
        if not wiz_element: return response.url
        data_p = wiz_element.get('data-p')
        obj = json.loads(data_p.replace('%.@.', '["garturlreq",'))
        payload = {'f.req': json.dumps([[['Fbv4je', json.dumps(obj[:-6] + obj[-2:]), 'null', 'generic']]])}
        api_url = "https://news.google.com/_/DotsSplashUi/data/batchexecute"
        post_resp = requests.post(api_url, headers=headers, data=payload, timeout=10)
        cleaned_response = post_resp.text.replace(")]}'", "").strip()
        response_data = json.loads(cleaned_response)
        article_url = json.loads(response_data[0][2])[1]
        return article_url
    except Exception as e:
        print(f"Error resolving: {e}")
        return google_url

test_urls = [
    "https://news.google.com/rss/articles/CBMipgFBVV95cUxNc1lSSmFGeFFrWFRwWHJWanB2UEJmUjRPUng3Wmw5TlB2MkR3T1RfQURnSnh0WnJoQ0VISFd6V2lzcE4xM3hZLXBNVTVHNlNmOG4wYTFmWGFmYzhNQlZUN215UHM5U3hMU2ZsbllHZHR2QlBJRjJTdmk1NmdRQkxMQy1GUGVPdVlTQjkxNHZ4MzZVODEyVTJYOWZfdS01MGlmcGkwMVRn?oc=5",
    "https://news.google.com/rss/articles/CBMisAFBVV95cUxPMF9KRWh5LUJKQnpsMkZsMUI5QWdZZDZldzhseFVqc21VSnBJamd4bFRSNHcxV285SVhBWEZxamZqNnV1a2haMFJRR2tvQWpJTlg0RVg4UXJZT2o3azBMZ203NURhR29TVTUxUTMycTlHc3ozWkJHN3M4bUxQQ2hsX2dSVzRBOXd6bGk1T0U4ZHo1R2FBdHlPZlRaMWNxUmJZMUZjT2l6MnhxakFUbTRzbg?oc=5",
    "https://www.seattletimes.com/business/retail/new-trader-joes-set-for-seattles-northgate-station/"
]

for google_url in test_urls:
    if "news.google.com" in google_url:
        url = resolve_google_url(google_url)
    else:
        url = google_url
        
    print(f"\nTesting: {url}")
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        print(f"Downloaded length: {len(downloaded)}")
        content = trafilatura.extract(downloaded, include_images=True, include_formatting=True, output_format='html')
        metadata = trafilatura.extract_metadata(downloaded)
        print(f"Title: {metadata.title if metadata else 'No Title'}")
        print("--- CONTENT SNIPPET ---")
        if content:
            print(content[:500])
            if "enable javascript" in content.lower() or "javascript is disabled" in content.lower():
                print("FOUND 'enable javascript' in extracted content!")
        else:
            print("No content extracted!")
    else:
        print("Failed to download!")
