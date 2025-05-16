# /models/User_Model.py
import json
import os
from typing import Dict, List, Union

class User:
    """
    Represents a user in the PokerBot system.
    """
    def __init__(self, id: int, username: str, email: str, password: str):
        """
        Initializes a User object.

        Args:
            id (int): The unique identifier for the user.
            username (str): The username of the user.
            email (str): The email address of the user.
            password (str): The password of the user.
        """
        self.id = id
        self.username = username
        self.email = email
        self.password = password

    def to_dict(self) -> Dict[str, Union[int, str]]:
        """
        Converts the User object to a dictionary.

        Returns:
            Dict[str, Union[int, str]]: A dictionary representation of the User.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "password": self.password,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Union[int, str]]) -> 'User':
        """
        Creates a User object from a dictionary.

        Args:
            data (Dict[str, Union[int, str]]): A dictionary containing user data.

        Returns:
            User: A User object.
        """
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
            password=data["password"],
        )

class User_Model:
    """
    Manages user data, providing methods for CRUD operations.
    """
    _DB_NAME = "users.json"  # Default database name
    _DATA_DIR = "data" # Directory where JSON files are stored.

    @classmethod
    def initialize_DB(cls, db_name: str = None) -> None:
        """
        Initializes the database (creates the JSON file if it doesn't exist).

        Args:
            db_name (str, optional): The name of the database file. Defaults to None.
        """
        if db_name:
            cls._DB_NAME = db_name
        if not os.path.exists(cls._DATA_DIR):
            os.makedirs(cls._DATA_DIR) #create data directory
        if not os.path.exists(os.path.join(cls._DATA_DIR, cls._DB_NAME)):
            with open(os.path.join(cls._DATA_DIR, cls._DB_NAME), "w") as f:
                json.dump([], f)

    @classmethod
    def _get_db_path(cls) -> str:
        """
        Helper method to get the full path to the database file.
        """
        return os.path.join(cls._DATA_DIR, cls._DB_NAME)
    
    @classmethod
    def _load_users(cls) -> List[Dict[str, Union[int, str]]]:
        """
        Loads user data from the JSON file.

        Returns:
            List[Dict[str, Union[int, str]]]: A list of user dictionaries.
        """
        try:
            with open(cls._get_db_path(), "r") as f:
                users_data = json.load(f)
            return users_data
        except FileNotFoundError:
            # Handle the case where the file doesn't exist (e.g., during initialization)
            return []
        except json.JSONDecodeError:
            # Handle the case where the file is empty or corrupted
            return []

    @classmethod
    def _save_users(cls, users_data: List[Dict[str, Union[int, str]]]) -> None:
        """
        Saves user data to the JSON file.

        Args:
            users_data (List[Dict[str, Union[int, str]]]): A list of user dictionaries.
        """
        with open(cls._get_db_path(), "w") as f:
            json.dump(users_data, f, indent=4)

    @classmethod
    def exists(cls, username: str = None, id: int = None) -> bool:
        """
        Checks if a user exists by username or ID.

        Args:
            username (str, optional): The username to check. Defaults to None.
            id (int, optional): The ID to check. Defaults to None.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        if username is None and id is None:
            raise ValueError("Either username or id must be provided.")

        users_data = cls._load_users()
        for user_data in users_data:
            if username is not None and user_data["username"] == username:
                return True
            if id is not None and user_data["id"] == id:
                return True
        return False

    @classmethod
    def create(cls, user_info: Dict[str, str]) -> User:
        """
        Creates a new user.

        Args:
            user_info (Dict[str, str]): A dictionary containing user information
                (username, email, password).

        Returns:
            User: The newly created User object.

        Raises:
            ValueError: If the username already exists.
        """
        if "username" not in user_info or "email" not in user_info or "password" not in user_info:
            raise ValueError("username, email, and password are required.")

        if cls.exists(username=user_info["username"]):
            raise ValueError(f"User with username '{user_info['username']}' already exists.")

        users_data = cls._load_users()
        next_id = 1 if not users_data else max(user["id"] for user in users_data) + 1
        new_user = User(id=next_id, **user_info)
        users_data.append(new_user.to_dict())
        cls._save_users(users_data)
        return new_user

    @classmethod
    def get(cls, username: str = None, id: int = None) -> Union[User, None]:
        """
        Retrieves a user by username or ID.

        Args:
            username (str, optional): The username to search for. Defaults to None.
            id (int, optional): The ID to search for. Defaults to None.

        Returns:
            Union[User, None]: The User object if found, None otherwise.

        Raises:
            ValueError: If neither username nor id is provided.
        """
        if username is None and id is None:
            raise ValueError("Either username or id must be provided.")

        users_data = cls._load_users()
        for user_data in users_data:
            if username is not None and user_data["username"] == username:
                return User.from_dict(user_data)
            if id is not None and user_data["id"] == id:
                return User.from_dict(user_data)
        return None

    @classmethod
    def get_all(cls) -> List[User]:
        """
        Retrieves all users.

        Returns:
            List[User]: A list of all User objects.
        """
        users_data = cls._load_users()
        return [User.from_dict(user_data) for user_data in users_data]

    @classmethod
    def update(cls, user_info: Dict[str, str]) -> User:
        """
        Updates an existing user.

        Args:
            user_info (Dict[str, str]): A dictionary containing the updated user information, including the user's id.

        Returns:
            User: The updated User object.

        Raises:
            ValueError: If the user ID is not provided or the user does not exist.
        """
        if "id" not in user_info:
            raise ValueError("User ID is required for updating.")

        user_id = user_info["id"]
        if not cls.exists(id=user_id):
            raise ValueError(f"User with ID '{user_id}' not found.")

        users_data = cls._load_users()
        for i, user_data in enumerate(users_data):
            if user_data["id"] == user_id:
                # Preserve the original ID.
                updated_user_data = {
                    "id": user_id,
                    "username": user_info.get("username", user_data["username"]), # Default to current value if not provided
                    "email": user_info.get("email", user_data["email"]),
                    "password": user_info.get("password", user_data["password"]),
                }
                users_data[i] = updated_user_data
                cls._save_users(users_data)
                return User.from_dict(updated_user_data)
        raise ValueError(f"User with ID '{user_id}' not found.") # added in case the loop finishes without finding the user.

    @classmethod
    def remove(cls, username: str) -> None:
        """
        Removes a user by username.

        Args:
            username (str): The username of the user to remove.

        Raises:
            ValueError: If the user does not exist.
        """
        if not cls.exists(username=username):
            raise ValueError(f"User with username '{username}' not found.")

        users_data = cls._load_users()
        for i, user_data in enumerate(users_data):
            if user_data["username"] == username:
                del users_data[i]
                cls._save_users(users_data)
                return
        raise ValueError(f"User with username '{username}' not found.")
