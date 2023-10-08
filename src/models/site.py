from typing import List, Optional
from pydantic import BaseModel, Field


class Site(BaseModel):
    # The name of the website.
    name: str
    # The main url for the website.
    main_url: str
    # The url to submit the user search too. Should be in python string format structure. EX: https://temp.com/u/{}
    user_url: str
    error_url: Optional[str]
    # "message" or "status_code"
    error_type: str
    # Indicates rather or not a website is NSFW
    nsfw: Optional[bool]
    # Indicates the username was found at this site.
    users_found: bool
    # The error message to search a 200 response code for.
    # This will help us determine if the response indicates the user was not found.
    error_message: Optional[str]

