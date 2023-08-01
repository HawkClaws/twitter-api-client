from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from twitter.model.tweet import Tweet
from twitter.model.user import User


class TweetData(BaseModel):
    tweet: Optional[Tweet] = None
    user: Optional[User] = None

