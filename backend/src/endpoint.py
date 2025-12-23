# system
import pandas as pd
import re
from datetime import datetime
from pydantic import BaseModel

# frameworks
from playwright.sync_api import sync_playwright
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from jose import JWTError, jwt

# local
from model import DogInfo, MemberInfo, CpeQuery, Token, VenueQuery, VenueUsersTable
from db import Database
from common import get_secret


app = FastAPI()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# For demonstration, replace with a secure secret key
SECRET_KEY = get_secret("JWT_SECRET_KEY")
ALGORITHM = "HS256"

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@app.post("/create-account")
async def create_account(form_data: OAuth2PasswordRequestForm = Depends()) -> bool:
    db = Database()
    print(f"IN create_account username={form_data.username}")
    user = db.get_user(form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {form_data.username} already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hashed_password = pwd_context.hash(form_data.password)
    result = db.create_user(form_data.username, hashed_password)
    if not result:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not create an account for user={form_data.username}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return result

@app.post("/change-password")
async def change_password(form_data: OAuth2PasswordRequestForm = Depends()) -> bool:
    db = Database()
    print(f"IN change_password username={form_data.username}")
    user = db.get_user(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user {form_data.username} does not exist",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hashed_password = pwd_context.hash(form_data.password)
    result = db.change_password(form_data.username, hashed_password)
    if not result:
        raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not change password for user={form_data.username}",
                headers={"WWW-Authenticate": "Bearer"},
            )
    return result

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = Database()
    user = db.get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/get-cpe-info/")
def get_cpe_info(query: CpeQuery, token: str = Depends(oauth2_scheme)) -> MemberInfo:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        sub = payload.get('sub')
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    db = Database()
    user_info = db.get_venue_user_info(user_id, 'CPE')
    if not user_info:
        raise HTTPException(status_code=404, detail=f"No user={user_id} for venue=CPE")

    venue_info = db.get_venue_info('CPE')
    if not venue_info:
        raise HTTPException(status_code=404, detail=f"No venue=CPE found")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(venue_info.url)
            page.fill("input[name='MemberIdOrEmailInput']", user_info.venue_user_id)
            page.fill("input[name='PasswordInput']", user_info.venue_password)
            page.locator('input[type="submit"]').click()
            page.wait_for_url(f"{venue_info.url}/Member/Records?isViewingActiveDogs=True")
        except TimeoutError:
            raise HTTPException(status_code=500, detail=f"Processing error for venue=CPE and user={user_info.venue_user_id}")
        
        handler, handler_member_id, address, phone, email = (None, None, None, None, None)
        address_div_locator = page.locator("#MemberInformation .address")
        address_pattern = re.compile(
            r'Member ID:(\d+)\n' # member_id
            r'Primary:(.+)\n' # handler
            r'Secondary:(.*)\n' # secondary
            r'Address:\n' # address
            r'(.*)',
            re.DOTALL)
        match = address_pattern .match(address_div_locator.inner_text())
        if match:
            handler_member_id, handler, _, address = match.groups()
        contact_div_locator = page.locator("#MemberInformation .contact-information")
        contact_pattern = re.compile(
            r'Dues Paid Through:(.+)\n' # info
            r'Phone [#]{1}1:(.+)\n' # phone_1
            r'Phone [#]{1}2:(.+)\n'
            r'Email:(.+)') 
        match = contact_pattern.match(contact_div_locator.inner_text())
        if match:
            _, phone, _, email = match.groups()
        
        table_data = []
        div_locator = page.locator("#DogList")
        rows = div_locator.locator("tr").all()
        for row in rows:
            row_data = []
            # Get all cells in the current row
            cells = row.locator("td").all() # Use 'th' for header cells if needed

            for cell in cells:
                cell_text = cell.inner_text()
                row_data.append(cell_text)
            if len(row_data) >= 5:
                table_data.append((handler_member_id, row_data[0], row_data[1], row_data[2], row_data[3], row_data[4]))

        dog_info_list = [DogInfo(dog_member_id=item[1], 
                                 call_name=item[2], 
                                 breed=item[3], 
                                 jump_height=int(item[4] if item[4] != "Needs Measurement" else "-1"), 
                                 dob=datetime.strptime(item[5], "%m/%d/%Y")) for item in table_data]
        member_info = MemberInfo(handler_member_id=handler_member_id,
                                 handler=handler,
                                 phone=phone,
                                 email=email,
                                 address=address,
                                 dog_info=dog_info_list)
        return member_info

@app.post("/get-venue-user-info/")
def get_venue_user_info(query: VenueQuery, token: str = Depends(oauth2_scheme)) -> VenueUsersTable:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        venue: str = query.venue
        sub = payload.get('sub')
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    db = Database()
    retval = db.get_venue_user_info(user_id, venue)
    if not retval:
        raise HTTPException(status_code=404, detail=f"No venue user info found for user_id={user_id}; venue={venue}")
    
    return retval

@app.post("/update-venue-user-info/")
def update_venue_user_info(data: VenueUsersTable, token: str = Depends(oauth2_scheme)) -> bool:
    print("IN update_venue_user_info")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get('sub')
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id = data.user_id
        venue = data.venue
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    db = Database()
    retval = db.update_venue_user_info(data)
    if not retval:
        raise HTTPException(status_code=404, detail=f"No venue user info found for user_id={user_id}; venue={venue}")
    print(f"OUT update_venue_user_info; retval={retval}")
    return retval