# system
import re
import pandas as pd
import bonobo
from datetime import datetime
from typing import List, Any, Dict, Generator, Tuple

from common import get_secret
from db import Database
from pydantic import BaseModel
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt

# local
from model import (  # noqa
    InfoQuery,
    DogInfo,
    MemberInfo,
    Token,
    VenueQuery,
    VenueUsersTable,
    ChainType
)
from passlib.context import CryptContext

# frameworks
from playwright.sync_api import sync_playwright

app = FastAPI()
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# For demonstration, replace with a secure secret key
SECRET_KEY = get_secret("JWT_SECRET_KEY")
ALGORITHM = "HS256"

# Global data
KV_STORE: Dict[ChainType, Any] = {}  # Key-Value storage for the transform results
PARAM_DICT: Dict[str, Any] = {}  # Key-Value storage to pass params

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
async def create_account(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> bool:
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
async def change_password(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> bool:
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
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
):
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
def get_cpe_info(
    query: InfoQuery, token: str = Depends(oauth2_scheme)
) -> MemberInfo:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return process_cpe_info_query(user_id)

def process_cpe_info_query(user_id: str) -> MemberInfo:
    db = Database()
    user_info = db.get_venue_user_info(user_id, "CPE")
    if not user_info:
        raise HTTPException(
            status_code=404, detail=f"No user={user_id} for venue=CPE"
        )

    venue_info = db.get_venue_info("CPE")[0]
    if not venue_info:
        raise HTTPException(status_code=404, detail="No venue=CPE found")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(venue_info.url)
            page.fill(
                "input[name='MemberIdOrEmailInput']", user_info.venue_user_id
            )
            page.fill("input[name='PasswordInput']", user_info.venue_password)
            page.locator('input[type="submit"]').click()
            page.wait_for_url(
                f"{venue_info.url}/Member/Records?isViewingActiveDogs=True"
            )
        except TimeoutError:
            detail = (
                "Processing error for venue=CPE and "
                + f"user={user_info.venue_user_id}"
            )
            raise HTTPException(status_code=500, detail=detail)

        handler, handler_member_id, address, phone, email = (
            None,
            None,
            None,
            None,
            None,
        )
        address_div_locator = page.locator("#MemberInformation .address")
        address_pattern = re.compile(
            r"Member ID:(\d+)\n"  # member_id
            r"Primary:(.+)\n"  # handler
            r"Secondary:(.*)\n"  # secondary
            r"Address:\n"  # address
            r"(.*)",
            re.DOTALL,
        )
        match = address_pattern.match(address_div_locator.inner_text())
        if match:
            handler_member_id, handler, _, address = match.groups()
        contact_div_locator = page.locator(
            "#MemberInformation .contact-information"
        )
        contact_pattern = re.compile(
            r"Dues Paid Through:(.+)\n"  # info
            r"Phone [#]{1}1:(.+)\n"  # phone_1
            r"Phone [#]{1}2:(.+)\n"
            r"Email:(.+)"
        )
        match = contact_pattern.match(contact_div_locator.inner_text())
        if match:
            _, phone, _, email = match.groups()

        table_data = []
        div_locator = page.locator("#DogList")
        rows = div_locator.locator("tr").all()
        for row in rows:
            row_data = []
            # Get all cells in the current row
            cells = row.locator("td").all()  # Use 'th' for header cells if needed

            for cell in cells:
                cell_text = cell.inner_text()
                row_data.append(cell_text)
            if len(row_data) >= 5:
                table_data.append(
                    (
                        handler_member_id,
                        row_data[0],
                        row_data[1],
                        row_data[2],
                        row_data[3],
                        row_data[4],
                    )
                )

        dog_info_list = [
            DogInfo(
                dog_member_id=item[1],
                call_name=item[2],
                breed=item[3],
                jump_height=int(
                    item[4] if item[4] != "Needs Measurement" else "-1"
                ),
                dob=datetime.strptime(item[5], "%m/%d/%Y"),
            )
            for item in table_data
        ]
        member_info = MemberInfo(
            venue=venue_info.venue,
            icon=venue_info.icon,
            description=venue_info.description,
            handler_member_id=handler_member_id,
            handler=handler,
            phone=phone,
            email=email,
            address=address,
            dog_info=dog_info_list,
        )
        return member_info


@app.post("/get-venue-user-info/")
def get_venue_user_info(
    query: VenueQuery, token: str = Depends(oauth2_scheme)
) -> VenueUsersTable:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        venue: str = query.venue
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db = Database()
    retval = db.get_venue_user_info(user_id, venue)
    if not retval:
        detail = (
            "No venue user info found for " + f"user_id={user_id}; venue={venue}"
        )
        raise HTTPException(status_code=404, detail=detail)

    return retval

@app.post("/get-user-venues/")
def get_user_venues(
    query: InfoQuery, token: str = Depends(oauth2_scheme)
) -> List[VenueUsersTable]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db = Database()
    user_venues = db.get_user_venues(user_id)
    if not user_venues:
        detail = (
            "No venue user info found for " + f"user_id={user_id}"
        )
        raise HTTPException(status_code=404, detail=detail)

    user_venue_set = set([user_venue.venue for user_venue in user_venues])
    system_venue_set = set([system_venue.venue for system_venue in db.get_venue_info()])
    working_set = system_venue_set.difference(user_venue_set)
    for venue in working_set:
        user_venues.append(VenueUsersTable(user_id=user_id, venue=venue, venue_user_id=None, venue_password=None))
    return user_venues

@app.post("/update-venue-user-info/")
def update_venue_user_info(
    data: VenueUsersTable, token: str = Depends(oauth2_scheme)
) -> bool:
    print("IN update_venue_user_info")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        user_id = data.user_id
        venue = data.venue
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    db = Database()
    retval = db.update_venue_user_info(data)
    if not retval:
        detail = (
            "No venue user info found for " + f"user_id={user_id}; venue={venue}"
        )
        raise HTTPException(status_code=404, detail=detail)
    print(f"OUT update_venue_user_info; retval={retval}")
    return retval


@app.post("/get-bha-info/")
def get_bha_info(
    query: InfoQuery, token: str = Depends(oauth2_scheme)
) -> MemberInfo:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return process_bha_info_query(user_id)

def process_bha_info_query(user_id: str) -> MemberInfo:
    db = Database()
    user_info = db.get_venue_user_info(user_id, "BHA")
    if not user_info:
        raise HTTPException(
            status_code=404, detail=f"No user={user_id} for venue=BHA"
        )

    venue_info = db.get_venue_info("BHA")[0]
    if not venue_info:
        raise HTTPException(status_code=404, detail="No venue=BHA found")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(f"{venue_info.url}/register/login.php")
            page.fill(
                "input[name='user']", user_info.venue_user_id
            )
            page.fill("input[name='pass']", user_info.venue_password)
            page.locator('input[type="submit"]').click()
            page.wait_for_url(
                f"{venue_info.url}/register/barn_hunt_dog_register.php"
            )
            page.goto(f"{venue_info.url}/register/your_profile.php")

            input_element = page.locator("[name='login_email']")
            handler_member_id = input_element.get_attribute('value')
            email = handler_member_id

            input_element = page.locator("[name='login_firstname']")
            firstname =  input_element.get_attribute('value')

            input_element = page.locator("[name='login_lastname']")
            lastname =  input_element.get_attribute('value')

            input_element = page.locator("[name='login_addr1']")
            addr1 = input_element.get_attribute('value')

            input_element = page.locator("[name='login_addr2']")
            addr2 = input_element.get_attribute('value')

            input_element = page.locator("[name='login_city']")
            city = input_element.get_attribute('value')

            input_element = page.locator("[name='login_postal']")
            zipcode = input_element.get_attribute('value')

            input_element = page.locator("[name='login_phone']")
            phone = input_element.get_attribute('value')

            select_element = page.locator("[name='login_state']")
            state = select_element.evaluate("select => select.value")

            address = f"{addr1}\n{addr2}\n{city}, {state} {zipcode}"


            page.goto(f"{venue_info.url}/register/your_dogs.php")
            table_locator = page.locator("table.data")
            rows = table_locator.locator("tr").all()
            columns = []
            table_data = []
            for index, row in enumerate(rows):
                # Get all cells in the current row
                cells = row.locator("td").all()  # Use 'th' for header cells if needed

                if index == 0:
                    columns = [cell.inner_text() for cell in cells]
                else:
                    table_data.append([cell.inner_text() for cell in cells])
            dogs_df = pd.DataFrame(table_data, columns=columns)
            print(dogs_df)
            dog_info = []
            for index, row in dogs_df.iterrows():
                info = DogInfo(dog_member_id=row['Barnhunt No'], 
                               call_name=row['Call Name'], 
                               breed=row['Breed'], 
                               jump_height=int(float(row['Height'])), 
                               dob=datetime.strptime(row['Birthdate'], "%m/%d/%Y"))
                dog_info.append(info)

            member_info = MemberInfo(
                venue=venue_info.venue,
                icon=venue_info.icon,
                description=venue_info.description,
                handler_member_id=handler_member_id,
                handler=f"{firstname} {lastname}",
                phone=phone,
                email=email,
                address=address,
                dog_info=dog_info,
            )
            print(member_info)
            return member_info
    
        except TimeoutError:
            detail = (
                "Processing error for venue=BHA and "
                + f"user={user_info.venue_user_id}"
            )
            raise HTTPException(status_code=500, detail=detail)

        
        return None


def store_results(key: ChainType, data: BaseModel):
    """
    Store transform results for final processing.

    Parameters
    ----------
    key : str
        The type of data (channel_data or comment_thread_data)
    df : pd.DataFrame
        The dataframe output by the transform function.
    """
    global KV_STORE
    print(f"IN store_results {key}")
    KV_STORE[key] = data

def extract_cpe_info() -> Generator[Tuple[ChainType, MemberInfo], None, None]:
    """
    Search for videos that match a query string.

    Parameters
    ----------
    query : str
        The query string used in the "q" parameter.

    Yields
    ------
    Generator[list[tuple[str, str]], None, None]
        A list of tuple pairs (video_id, channel_id)
    """
    cpe_info = process_cpe_info_query(PARAM_DICT['user_id'])
    yield (ChainType.CPE_DATA, cpe_info)

def extract_bha_info() -> Generator[Tuple[ChainType, MemberInfo], None, None]:
    """
    Search for videos that match a query string.

    Parameters
    ----------
    query : str
        The query string used in the "q" parameter.

    Yields
    ------
    Generator[list[tuple[str, str]], None, None]
        A list of tuple pairs (video_id, channel_id)
    """
    bha_info = process_bha_info_query(PARAM_DICT['user_id'])
    yield (ChainType.BHA_DATA, bha_info)

@app.post("/get-user-info/")
def get_user_info(
    query: InfoQuery, token: str = Depends(oauth2_scheme)
) -> List[MemberInfo]:
    global KV_STORE
    member_info_list = []
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = query.user_id
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    db = Database()
    user_info_list = db.get_user_venues(user_id)
    
    
    graph = bonobo.Graph()
    graph.add_chain(store_results, _input=None)

    venues = [user_info.venue for user_info in user_info_list]
    PARAM_DICT['user_id'] = user_id
    if 'CPE' in venues:
        graph.add_chain(
            extract_cpe_info,
            store_results,
        )
    if 'BHA' in venues:
        graph.add_chain(
            extract_bha_info,
            store_results,
        )
    bonobo.run(graph)

    for k, v in KV_STORE.items():
        member_info_list.append(v)
    
    KV_STORE = {}
    return member_info_list

if __name__ == "__main__":
    query = InfoQuery(user_id="sdimig")
    get_bha_info(query)
