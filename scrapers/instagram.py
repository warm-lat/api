import httpx
import re
import json
import os
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List

COOKIES_FILE = os.path.join(os.path.dirname(__file__), "..", "cookies.txt")

BASE_URL = "https://www.instagram.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def load_cookies() -> Dict[str, str]:
    cookies = {}
    if os.path.exists(COOKIES_FILE):
        with open(COOKIES_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split("\t")
                    if len(parts) >= 7:
                        cookies[parts[5]] = parts[6]
    return cookies


async def get_page(url: str) -> str:
    cookies = load_cookies()
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(url, headers=HEADERS, cookies=cookies)
        response.raise_for_status()
        return response.text


def extract_shared_data(html: str) -> Dict[str, Any]:
    script_pattern = r"window\._sharedData\s*=\s*({.+?});</script>"
    match = re.search(script_pattern, html)
    if match:
        return json.loads(match.group(1))
    return {}


async def get_user_profile(username: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/{username}/"
    html = await get_page(url)
    shared_data = extract_shared_data(html)
    
    entry_data = shared_data.get("entry_data", {}).get("ProfilePage", [{}])[0]
    user_data = entry_data.get("graphql", {}).get("user", {})
    
    if not user_data:
        return None
    
    return {
        "id": user_data.get("id"),
        "username": user_data.get("username"),
        "full_name": user_data.get("full_name"),
        "biography": user_data.get("biography"),
        "followers_count": user_data.get("edge_followed_by", {}).get("count"),
        "following_count": user_data.get("edge_follow", {}).get("count"),
        "posts_count": user_data.get("edge_owner_to_timeline_media", {}).get("count"),
        "profile_pic_url": user_data.get("profile_pic_url"),
        "profile_pic_url_hd": user_data.get("profile_pic_url_hd"),
        "is_private": user_data.get("is_private"),
        "is_verified": user_data.get("is_verified"),
        "external_url": user_data.get("external_url"),
        "is_business": user_data.get("is_business"),
    }


async def get_user_posts(username: str, count: int = 12) -> List[Dict[str, Any]]:
    url = f"{BASE_URL}/{username}/"
    html = await get_page(url)
    shared_data = extract_shared_data(html)
    
    entry_data = shared_data.get("entry_data", {}).get("ProfilePage", [{}])[0]
    user_data = entry_data.get("graphql", {}).get("user", {})
    
    if not user_data:
        return []
    
    posts = []
    media_edges = user_data.get("edge_owner_to_timeline_media", {}).get("edges", [])
    
    for edge in media_edges[:count]:
        node = edge.get("node", {})
        posts.append({
            "id": node.get("id"),
            "shortcode": node.get("shortcode"),
            "thumbnail_src": node.get("thumbnail_src"),
            "display_url": node.get("display_url"),
            "is_video": node.get("is_video"),
            "taken_at_timestamp": node.get("taken_at_timestamp"),
            "likes_count": node.get("edge_liked_by", {}).get("count"),
            "comments_count": node.get("edge_media_to_comment", {}).get("count"),
            "caption": node.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text"),
            "accessibility_caption": node.get("accessibility_caption"),
        })
    
    return posts


async def get_post_by_shortcode(shortcode: str) -> Optional[Dict[str, Any]]:
    url = f"{BASE_URL}/p/{shortcode}/"
    html = await get_page(url)
    shared_data = extract_shared_data(html)
    
    entry_data = shared_data.get("entry_data", {}).get("PostPage", [{}])[0]
    media_data = entry_data.get("graphql", {}).get("shortcode_media", {})
    
    if not media_data:
        return None
    
    return {
        "id": media_data.get("id"),
        "shortcode": media_data.get("shortcode"),
        "display_url": media_data.get("display_url"),
        "thumbnail_src": media_data.get("thumbnail_src"),
        "is_video": media_data.get("is_video"),
        "video_url": media_data.get("video_url"),
        "taken_at_timestamp": media_data.get("taken_at_timestamp"),
        "likes_count": media_data.get("edge_liked_by", {}).get("count"),
        "comments_count": media_data.get("edge_media_to_comment", {}).get("count"),
        "caption": media_data.get("edge_media_to_caption", {}).get("edges", [{}])[0].get("node", {}).get("text"),
        "accessibility_caption": media_data.get("accessibility_caption"),
        "owner": {
            "id": media_data.get("owner", {}).get("id"),
            "username": media_data.get("owner", {}).get("username"),
            "profile_pic_url": media_data.get("owner", {}).get("profile_pic_url"),
        },
    }
