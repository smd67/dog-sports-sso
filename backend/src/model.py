from datetime import date
from typing import List, Optional

from pydantic import BaseModel
from enum import Enum

class DogInfo(BaseModel):
    dog_member_id: str
    call_name: str
    breed: str
    jump_height: int
    dob: date


class MemberInfo(BaseModel):
    venue: str
    icon: str
    description: str
    handler_member_id: str
    handler: str
    address: str
    phone: str
    email: str
    dog_info: List[DogInfo]


class InfoQuery(BaseModel):
    user_id: str

class VenueQuery(BaseModel):
    user_id: str
    venue: str


class VenueUsersTable(BaseModel):
    user_id: str
    venue: str
    venue_user_id: Optional[str] = None
    venue_password:Optional[str] = None


class VenuesTable(BaseModel):
    venue: str
    url: str
    icon: str
    description: str


class UserInDB(BaseModel):
    username: str
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class ChainType(Enum):
    """
    Enumeration of graph chain types.
    """

    CPE_DATA = 1
    BHA_DATA = 2
