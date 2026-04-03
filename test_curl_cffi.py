from curl_cffi import requests
import trafilatura

url = "https://medium.com/blog/after-a-year-of-vibe-coding-ai-still-cant-replace-effort-expertise-00c9aa44ee28"

print(f"Testing Medium with curl_cffi: {url}")
try:
    # impersonate='chrome' is the magic for Cloudflare
    response = requests.get(url, impersonate="chrome", timeout=15)
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
        print(f"Failed to download! Body snippet: {response.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
