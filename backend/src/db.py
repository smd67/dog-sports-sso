import pymysql
import os
from model import VenueUsersTable, VenuesTable, UserInDB
from common import get_secret

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_initialized'):  # Prevent re-initialization
            self.mysql_user = os.environ.get('MYSQL_USER')
            self.mysql_passwd = get_secret('MYSQL_PASSWORD')
            self.mysql_database = os.environ.get('MYSQL_DATABASE')
            try:
                # Establish a connection to the MySQL database
                self.connection = pymysql.connect(host='host.docker.internal',
                                                  user=self.mysql_user,
                                                  password=self.mysql_passwd,
                                                  database=self.mysql_database)
                setattr(self, '_initialized', True)
            except Exception as e:
                print(f"Error unexpected exception in Database::__init__. e={e}")
                raise e

    def get_venue_user_info(self, user_id: str, venue: str) -> VenueUsersTable:
        print("IN get_venue_user_info")
        user_info = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = f"SELECT * FROM venue_users WHERE user_id='{user_id}' AND venue='{venue}' LIMIT 1"
            print(f"SQL={sql}")
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            if results:
                user_info = VenueUsersTable(user_id=results[0][0], 
                                            venue=results[0][1], 
                                            venue_user_id=results[0][2], 
                                            venue_password=results[0][3])
        print(f"OUT get_venue_user_info. user_info={user_info}")
        return user_info
    
    def update_venue_user_info(self, data: VenueUsersTable) -> bool:
        print("IN update_venue_user_info")
        user_id = data.user_id
        venue = data.venue
        venue_user_id = data.venue_user_id
        venue_password = data.venue_password

        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            retval = True
            try:
                # Execute an SQL query
                sql = f"REPLACE INTO venue_users (user_id, venue, venue_user_id, venue_password) VALUES ('{user_id}', '{venue}', '{venue_user_id}', '{venue_password}');"
                print(f"SQL={sql}")
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False
        print(f"OUT update_venue_user_info. retval={retval}")
        return retval

    def get_venue_info(self, venue: str) -> VenuesTable:
        venue_info = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = f"SELECT * FROM venues WHERE venue='{venue}' LIMIT 1"
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            if results:
                venue_info = VenuesTable(venue=results[0][0], url=results[0][1])
                
        return venue_info
    
    def get_user(self, username: str) -> UserInDB:
        user_in_db = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = f"SELECT * FROM users WHERE user_id='{username}' LIMIT 1"
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            if results:
                user_in_db = UserInDB(username=results[0][0], hashed_password=results[0][1])
        
        return user_in_db
    
    def create_user(self, username: str, password: str) -> bool:
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            retval = True
            try:
                # Execute an SQL query
                sql = f"INSERT INTO users (user_id, password) VALUES ('{username}', '{password}');"
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False

        return retval
    
    def change_password(self, username: str, password: str) -> bool:
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            retval = True
            try:
                # Execute an SQL query
                sql = f"UPDATE users SET password='{password}' WHERE user_id='{username}';"
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False

        return retval
