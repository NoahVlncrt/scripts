import trafilatura

url = "https://abcnews.go.com/International/stunning-new-photos-show-earth-orion-capsule/story?id=108842426" # Example URL from the feed
downloaded = trafilatura.fetch_url(url)
if downloaded:
    content = trafilatura.extract(downloaded, include_images=True, include_formatting=True, output_format='html')
    metadata = trafilatura.extract_metadata(downloaded)
    print("--- METADATA IMAGE ---")
    print(metadata.image if metadata else "No image")
    print("--- CONTENT SNIPPET ---")
    print(content[:1000] if content else "No content")
else:
    print("Failed to download")
