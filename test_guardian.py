import requests
import trafilatura

url = "https://www.theguardian.com/science/2026/apr/03/artemis-ii-astronauts-pass-100000-miles-from-earth-on-voyage-to-the-moon"
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
        image = getattr(metadata, 'image', None)
        print(image if image else "No image")
        print("--- CONTENT SNIPPET ---")
        print(content[:1000] if content else "No content")
except Exception as e:
    print(f"Error: {e}")
