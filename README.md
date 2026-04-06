# Google News RSS Content Resolver

A Python-based tool that takes Google News RSS feeds, resolves their redirect URLs to the original source articles, extracts the full text (bypassing many paywalls/Cloudflare using `curl_cffi`), and generates a new, clean RSS feed with the full article content.

> [!CAUTION]
> **DISCLAIMER:** This project is almost entirely **AI-generated**. I am using it "as-is" because I thought the functionality was cool and decided to share it. Use at your own risk.

## Features

- **URL Resolution:** Decodes the complex Google News redirect URLs to get direct links.
- **Content Extraction:** Uses `trafilatura` and `curl_cffi` to extract clean article text and images.
- **Multi-Search Support:** Configure multiple search queries in a single JSON file.
- **National Publisher Filtering:** Automatically filters for high-quality national news sources.
- **Caching:** Saves previously resolved articles to `cache.json` to speed up subsequent runs and respect site bandwidth.
- **GitHub Actions Integration:** Automatically runs on a schedule to keep your feeds updated.

## Configuration

You can add or modify searches by editing `searches.json`:

```json
[
  {
    "name": "Topic Name",
    "url": "https://news.google.com/rss/search?q=Your+Query...",
    "output": "output_filename.xml"
  }
]
```

## Setup & Usage

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Resolver:**
   ```bash
   python resolve_news.py
   ```
   This will process all searches defined in `searches.json` and generate the corresponding `.xml` files.

## 🚀 Automation with GitHub Actions

This project is fully automated! Using GitHub Actions, the resolver runs on a **set schedule** multiple times a day to ensure your RSS feeds are always fresh and up-to-date without you ever having to lift a finger.

- **Set and Forget:** The pre-configured workflow handles everything—from fetching the latest news to extracting full text and updating your feeds.
- **Auto-Commit:** Any new articles found are automatically committed and pushed back to your repository, so you can point your RSS reader at the raw XML URLs.
- **Manual Trigger:** Want an update *right now*? You can manually trigger the workflow at any time from the "Actions" tab in your GitHub repository.

To use this, just push this project to a GitHub repository, and the automation will take over!

## Credits & Tools
- [curl_cffi](https://github.com/yifeikong/curl_cffi) - For browser-like TLS fingerprints.
- [trafilatura](https://trafilatura.readthedocs.io/) - For high-quality web scraping and text extraction.
- [feedparser](https://github.com/kurtmckee/feedparser) - For RSS handling.
