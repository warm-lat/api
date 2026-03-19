from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional

from auth import verify_api_key_with_increment
from scrapers import instagram

router = APIRouter()


@router.get("/instagram/profile/{username}")
async def get_instagram_profile(
    username: str,
    api_key_data: dict = Depends(verify_api_key_with_increment)
):
    profile = await instagram.get_user_profile(username)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/instagram/posts/{username}")
async def get_instagram_posts(
    username: str,
    count: int = 12,
    api_key_data: dict = Depends(verify_api_key_with_increment)
):
    posts = await instagram.get_user_posts(username, count)
    return {"username": username, "posts": posts}


@router.get("/instagram/post/{shortcode}")
async def get_instagram_post(
    shortcode: str,
    api_key_data: dict = Depends(verify_api_key_with_increment)
):
    post = await instagram.get_post_by_shortcode(shortcode)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
