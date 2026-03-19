import os
import asyncio
from datetime import datetime
from typing import Optional
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None and DATABASE_URL:
        _pool = await asyncpg.create_pool(
            dsn=DATABASE_URL,
            min_size=2,
            max_size=10
        )
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def validate_api_key(api_key: str) -> Optional[dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, key, name, owner_id, rate_limit, requests_today, 
                   total_requests, created_at, expires_at, is_active
            FROM api_keys
            WHERE key = $1 AND is_active = true
            """,
            api_key
        )
        
        if row is None:
            return None
        
        expires_at = row["expires_at"]
        if expires_at and expires_at < datetime.now():
            return None
        
        return dict(row)


async def increment_request_count(api_key_id: int, requests_today: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        new_total = requests_today + 1
        await conn.execute(
            """
            UPDATE api_keys 
            SET requests_today = $1, total_requests = total_requests + 1
            WHERE id = $2
            """,
            new_total, api_key_id
        )


async def reset_daily_requests():
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE api_keys SET requests_today = 0"
        )


async def check_rate_limit(api_key: str) -> tuple[bool, Optional[str]]:
    key_data = await validate_api_key(api_key)
    if key_data is None:
        return False, "Invalid or expired API key"
    
    if key_data["requests_today"] >= key_data["rate_limit"]:
        return False, "Rate limit exceeded"
    
    return True, None
