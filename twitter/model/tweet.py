from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Entities(BaseModel):
    user_mentions: List
    urls: List
    hashtags: List
    symbols: List


class Tweet(BaseModel):
    bookmark_count: Optional[int] = None
    bookmarked: Optional[bool] = None
    created_at: Optional[str] = None
    conversation_id_str: Optional[str] = None
    display_text_range: Optional[List[int]] = None
    entities: Optional[Entities] = None
    favorite_count: Optional[int] = None
    favorited: Optional[bool] = None
    full_text: Optional[str] = None
    is_quote_status: Optional[bool] = None
    lang: Optional[str] = None
    quote_count: Optional[int] = None
    reply_count: Optional[int] = None
    retweet_count: Optional[int] = None
    retweeted: Optional[bool] = None
    user_id_str: Optional[str] = None
    id_str: Optional[str] = None
