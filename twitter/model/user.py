from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class Description(BaseModel):
    urls: List


class Entities(BaseModel):
    description: Description


class User(BaseModel):
    user_id: Optional[str] = None
    followed_by: Optional[bool] = None
    following: Optional[bool] = None
    can_dm: Optional[bool] = None
    can_media_tag: Optional[bool] = None
    created_at: Optional[str] = None
    default_profile: Optional[bool] = None
    default_profile_image: Optional[bool] = None
    description: Optional[str] = None
    entities: Optional[Entities] = None
    fast_followers_count: Optional[int] = None
    favourites_count: Optional[int] = None
    followers_count: Optional[int] = None
    friends_count: Optional[int] = None
    has_custom_timelines: Optional[bool] = None
    is_translator: Optional[bool] = None
    listed_count: Optional[int] = None
    location: Optional[str] = None
    media_count: Optional[int] = None
    name: Optional[str] = None
    normal_followers_count: Optional[int] = None
    pinned_tweet_ids_str: Optional[List[str]] = None
    possibly_sensitive: Optional[bool] = None
    profile_banner_url: Optional[str] = None
    profile_image_url_https: Optional[str] = None
    profile_interstitial_type: Optional[str] = None
    screen_name: Optional[str] = None
    statuses_count: Optional[int] = None
    translator_type: Optional[str] = None
    verified: Optional[bool] = None
    want_retweets: Optional[bool] = None
    withheld_in_countries: Optional[List] = None
