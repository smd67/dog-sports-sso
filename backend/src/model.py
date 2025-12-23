from pydantic import BaseModel
from typing import Any, List
from datetime import date

class DogInfo(BaseModel):
    dog_member_id: str
    call_name: str
    breed: str
    jump_height: int
    dob: date

class MemberInfo(BaseModel):
    handler_member_id: str
    handler: str
    address: str
    phone: str
    email: str
    dog_info: List[DogInfo]

class CpeQuery(BaseModel):
    user_id: str

class VenueQuery(BaseModel):
    user_id: str
    venue: str

class VenueUsersTable(BaseModel):
    user_id: str
    venue: str
    venue_user_id: str
    venue_password: str

class VenuesTable(BaseModel):
    venue: str
    url: str

class UserInDB(BaseModel):
    username: str
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
