import requests
import trafilatura

url = "https://www.bbc.com/news/science-environment-68725208"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        content = trafilatura.extract(response.text, include_images=True, include_formatting=True, output_format='html')
        metadata = trafilatura.extract_metadata(response.text)
        print("--- METADATA IMAGE ---")
        print(metadata.image if metadata and hasattr(metadata, 'image') else "No image")
        print("--- CONTENT SNIPPET ---")
        print(content[:500] if content else "No content")
except Exception as e:
    print(f"Error: {e}")
