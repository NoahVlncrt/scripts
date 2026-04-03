import trafilatura

urls = [
    "https://www.wired.com/story/even-artemis-ii-astronauts-have-microsoft-outlook-problems/",
    "https://www.bbc.com/news/science-environment-68725208"
]

for url in urls:
    print(f"Testing {url}...")
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        content = trafilatura.extract(downloaded, include_images=True, include_formatting=True, output_format='html')
        metadata = trafilatura.extract_metadata(downloaded)
        print("--- METADATA IMAGE ---")
        print(metadata.image if metadata else "No image")
        print("--- CONTENT SNIPPET ---")
        print(content[:500] if content else "No content")
    else:
        print("Failed to download")
    print("-" * 20)
