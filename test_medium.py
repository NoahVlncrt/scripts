import requests
import trafilatura

url = "https://medium.com/blog/after-a-year-of-vibe-coding-ai-still-cant-replace-effort-expertise-00c9aa44ee28"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
}

print(f"Testing Medium with requests: {url}")
try:
    response = requests.get(url, headers=headers, timeout=15)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Downloaded length: {len(response.text)}")
        content = trafilatura.extract(response.text, include_images=True, include_formatting=True, output_format='html')
        if content:
            print("--- CONTENT SNIPPET ---")
            print(content[:1000])
        else:
            print("No content extracted!")
            print("--- RAW HTML PREVIEW ---")
            print(response.text[:1000])
    else:
        print(f"Failed to download! Body: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
