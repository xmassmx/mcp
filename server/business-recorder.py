from typing import Any, Literal
import httpx
from mcp.server.fastmcp import FastMCP
import feedparser

# Initialize FastMCP server
mcp = FastMCP("news")

BASE_URL = "https://www.brecorder.com/feeds/"

async def rss_handler(feed_url, max_items=10):
    """
    Fetches the RSS feed from the given URL and prints out the latest entries.

    Args:
        feed_url (str): URL of the RSS feed
        max_items (int): Maximum number of items to display
    """
    feed = feedparser.parse(feed_url)

    fields = ['id', 'title', 'link', 'published', 'summary', 'authors']
    feed = feedparser.parse(feed_url)
    results = []

    for entry in feed.entries[:max_items]:
        item = {}
        for key in fields:
            # Use entry.get to safely fetch values; default to None if missing
            item[key] = entry.get(key)
        results.append(item)

    return results

@mcp.tool()
async def get_news(news_type: Literal["latest", "markets", "world", "pakistan"], max_items: int = 5) -> list:
    """Get news from Business Recorder based on the specified type

    Args:
        news_type: The type of news to fetch. Can be one of: "latest", "markets", "world", "pakistan"
        max_items: The maximum number of items to return
    """
    feed_mapping = {
        "latest": "latest-news",
        "markets": "markets",
        "world": "world",
        "pakistan": "pakistan"
    }
    
    feed_path = feed_mapping.get(news_type)
    if not feed_path:
        raise ValueError(f"Invalid news type. Must be one of: {list(feed_mapping.keys())}")
        
    entries = await rss_handler(BASE_URL + feed_path, max_items)
    return entries

@mcp.tool()
async def get_entry_detail(news_type: Literal["latest", "markets", "world", "pakistan"], id: str) -> list:
    """Get more details of a particular article given its id.

    Args:
        news_type: The type of news to fetch. Can be one of: "latest", "markets", "world", "pakistan"
        id: id of the news to get more information of
    """
    feed_mapping = {
        "latest": "latest-news",
        "markets": "markets",
        "world": "world",
        "pakistan": "pakistan"
    }
    feed_path = feed_mapping.get(news_type)
    entries = await rss_handler(BASE_URL+feed_path,20)
    matches = []
    for entry in entries:
        if entry.get("id") == id or entry.get("link", "").rstrip("/").endswith(id):
            matches.append(entry)

    return matches

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')