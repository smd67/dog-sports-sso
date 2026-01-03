"""
This file contains an implementation of a singleton class for database access.
"""

import os

import pymysql
from common import get_secret
from model import UserInDB, VenuesTable, VenueUsersTable
from typing import List


class Database:
    """
    Singleton class for database access.
    """

    _instance = None

    # def __new__(cls, *args, **kwargs):
    #     """
    #     This method is executed when a new instance is instantiated.
    #     """
    #     if cls._instance is None:
    #         cls._instance = super().__new__(cls)
    #     return cls._instance

    def __init__(self):
        """
        Constructor for the Database class.

        Raises
        ------
        e
            Will rethrow any exceptions encountered connecting to the database.
        """
        # if not hasattr(self, "_initialized"):  # Prevent re-initialization
        self.mysql_user = os.environ.get("MYSQL_USER")
        self.mysql_passwd = get_secret("MYSQL_PASSWORD")
        self.mysql_database = os.environ.get("MYSQL_DATABASE")
        try:
            # Establish a connection to the MySQL database
            self.connection = pymysql.connect(
                host="host.docker.internal",
                #host="localhost",
                user=self.mysql_user,
                password=self.mysql_passwd,
                database=self.mysql_database,
            )
        #    setattr(self, "_initialized", True)
        except Exception as e:
            print(f"Error unexpected exception in Database::__init__. e={e}")
            raise e

    def get_venue_user_info(self, user_id: str, venue: str) -> VenueUsersTable:
        """
        Get user information for a particular venue.

        Parameters
        ----------
        user_id : str
            The sso user id.
        venue : str
            The venue to return information about.

        Returns
        -------
        VenueUsersTable
            A row from the venue_users table.
        """
        print("IN get_venue_user_info")
        user_info = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = (
                f"SELECT * FROM venue_users WHERE user_id='{user_id}' "
                + f"AND venue='{venue}' LIMIT 1"
            )

            print(f"SQL={sql}")
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            if results:
                user_info = VenueUsersTable(
                    user_id=results[0][0],
                    venue=results[0][1],
                    venue_user_id=results[0][2],
                    venue_password=results[0][3],
                )
        print(f"OUT get_venue_user_info. user_info={user_info}")
        return user_info

    def get_user_venues(self, user_id: str) -> List[VenueUsersTable]:
        """
        Get user information for all venues.

        Parameters
        ----------
        user_id : str
            The sso user id.

        Returns
        -------
        List[VenueUsersTable]
            Rows from the venue_users table.
        """
        print("IN get_user_venues")
        user_info = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = (
                f"SELECT * FROM venue_users WHERE user_id='{user_id}'"
            )

            print(f"SQL={sql}")
            cursor.execute(sql)

            user_info_list = []
            # Fetch all results
            results = cursor.fetchall()
            for row in results:
                print(f"row={row}")
                user_info = VenueUsersTable(
                    user_id=row[0],
                    venue=row[1],
                    venue_user_id=row[2],
                    venue_password=row[3],
                )
                user_info_list.append(user_info)

        print(f"OUT get_user_venues. user_info_list={user_info_list}")
        return user_info_list
    
    def update_venue_user_info(self, data: VenueUsersTable) -> bool:
        """
        Updates the venue_users table 

        Parameters
        ----------
        data : VenueUsersTable
            A row from the venue_users table

        Returns
        -------
        bool
            True is returned if the update was successful, False otherwise.
        """
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
                sql = (
                    "REPLACE INTO venue_users (user_id, venue, venue_user_id, "
                    + "venue_password) "
                    + f"VALUES ('{user_id}', '{venue}', '{venue_user_id}', "
                    + f"'{venue_password}');"
                )
                print(f"SQL={sql}")
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False
        print(f"OUT update_venue_user_info. retval={retval}")
        return retval

    def get_venue_info(self, venue: str = None) -> List[VenuesTable]:
        """
        Return information for a given venue.

        Parameters
        ----------
        venue : str
            The venue to query for (ie; 'CPE')

        Returns
        -------
        VenuesTable
            A row from the venues table.
        """
        venue_info = []
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = f"SELECT * FROM venues WHERE venue='{venue}' LIMIT 1" if venue else "SELECT * FROM venues"
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            venue_info = [VenuesTable(venue=row[0], url=row[1], icon=row[2], description=row[3]) for row in results]

        return venue_info

    def get_user(self, username: str) -> UserInDB:
        """
        Return a row of information about a user.

        Parameters
        ----------
        username : str
            The sso user id of the user

        Returns
        -------
        UserInDB
            A row from the users table in the database
        """
        user_in_db = None
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            # Execute an SQL query
            sql = f"SELECT * FROM users WHERE user_id='{username}' LIMIT 1"
            cursor.execute(sql)

            # Fetch all results
            results = cursor.fetchall()
            if results:
                user_in_db = UserInDB(
                    username=results[0][0], hashed_password=results[0][1]
                )

        return user_in_db

    def create_user(self, username: str, password: str) -> bool:
        """
        Create an sso user entry.

        Parameters
        ----------
        username : str
            The sso user id for the user
        password : str
            The password for the user

        Returns
        -------
        bool
            True is returned if the user is created successfully, False otherwise.
        """
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            retval = True
            try:
                # Execute an SQL query
                sql = (
                    "INSERT INTO users (user_id, password) "
                    + f"VALUES ('{username}', '{password}');"
                )
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False

        return retval

    def change_password(self, username: str, password: str) -> bool:
        """
        Change the password associate with an sso user id.

        Parameters
        ----------
        username : str
            The sso user id 
        password : str
            The new password value

        Returns
        -------
        bool
            True is returned if the password is updated successfully, False otherwise.
        """
        # Create a cursor object to execute SQL queries
        with self.connection.cursor() as cursor:
            retval = True
            try:
                # Execute an SQL query
                sql = (
                    f"UPDATE users SET password='{password}' "
                    + f"WHERE user_id='{username}';"
                )
                cursor.execute(sql)
                self.connection.commit()
            except Exception as e:
                print(f"Error: user creation error e={e}")
                retval = False

        return retval
