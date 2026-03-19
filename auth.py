from fastapi import Header, HTTPException, status
from typing import Annotated

from db import validate_api_key, increment_request_count


async def verify_api_key(x_api_key: Annotated[str, Header()]):
    key_data = await validate_api_key(x_api_key)
    if key_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    return key_data


async def verify_api_key_with_increment(x_api_key: Annotated[str, Header()]):
    key_data = await validate_api_key(x_api_key)
    if key_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    if key_data["requests_today"] >= key_data["rate_limit"]:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    
    await increment_request_count(key_data["id"], key_data["requests_today"])
    return key_data
