from typing import List, Optional
from pydantic import BaseModel, Field


class Site(BaseModel):
    name: str
    main_url: str
    user_url: str
    error_url: Optional[str]
    error_type: str
    nsfw: Optional[bool]
    users_found: List[str]
    error_message: Optional[str]

