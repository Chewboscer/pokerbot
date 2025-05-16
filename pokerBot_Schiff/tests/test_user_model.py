import pytest
import json
from models.user_model import User, User_Model
from .sample_user_data import sample_users  # Import sample data

# Use a consistent database name for testing
TEST_DB_NAME = "test_users.json"

@pytest.fixture(autouse=True)
def setup_database():
    """
    Fixture to initialize the database before each test.  This ensures
    a clean state for every test.  It recreates the database file
    with the sample user data.
    """
    User_Model.initialize_DB(TEST_DB_NAME)  # Use the test-specific DB name.
    # Populate the database with sample data.
    with open(User_Model._get_db_path(), "w") as f:
        json.dump(sample_users, f, indent=4)

def test_initialize_db():
    """
    Test that the database file is created if it doesn't exist.
    """
    # This test checks the setup_database fixture works correctly.
    assert os.path.exists(User_Model._get_db_path()), "Database file should exist."

def test_exists_by_username():
    """
    Test that the exists method returns True if a user exists by username.
    """
    assert User_Model.exists(username="john_doe")
    assert not User_Model.exists(username="nonexistent_user")

def test_exists_by_id():
    """
    Test that the exists method returns True if a user exists by ID.
    """
    assert User_Model.exists(id=1)
    assert not User_Model.exists(id=999)

def test_exists_with_no_arguments():
    """
    Test that exists raises a ValueError if no arguments are provided.
    """
    with pytest.raises(ValueError):
        User_Model.exists()

def test_create_user():
    """
    Test that a new user can be created successfully.
    """
    new_user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test_password",
    }
    new_user = User_Model.create(new_user_data)
    assert isinstance(new_user, User)
    assert User_Model.exists(username="test_user")
    assert new_user.username == "test_user"
    assert new_user.email == "test@example.com"
    assert new_user.password == "test_password"

def test_create_duplicate_user():
    """
    Test that creating a user with an existing username raises a ValueError.
    """
    with pytest.raises(ValueError):
        User_Model.create(sample_users[0])  # Use data from an existing user

def test_create_user_missing_fields():
    """
    Test that creating a user with missing fields raises a ValueError
    """
    with pytest.raises(ValueError):
        User_Model.create({"username": "test_user", "email": "test@example.com"})
    with pytest.raises(ValueError):
        User_Model.create({"username": "test_user", "password": "test_password"})
    with pytest.raises(ValueError):
        User_Model.create({"email": "test@example.com", "password": "test_password"})

def test_get_user_by_username():
    """
    Test that a user can be retrieved by username.
    """
    user = User_Model.get(username="jane_smith")
    assert isinstance(user, User)
    assert user.username == "jane_smith"
    assert user.email == "jane.smith@example.com"

def test_get_user_by_id():
    """
    Test that a user can be retrieved by ID.
    """
    user = User_Model.get(id=3)
    assert isinstance(user, User)
    assert user.username == "alice_johnson"
    assert user.email == "alice.johnson@example.com"

def test_get_nonexistent_user():
    """
    Test that get returns None for a non-existent user.
    """
    user_by_username = User_Model.get(username="nonexistent_user")
    user_by_id = User_Model.get(id=999)
    assert user_by_username is None
    assert user_by_id is None

def test_get_user_with_no_arguments():
    """
    Test that get raises a ValueError if no arguments are provided.
    """
    with pytest.raises(ValueError):
        User_Model.get()

def test_get_all_users():
    """
    Test that get_all returns a list of all users.
    """
    users = User_Model.get_all()
    assert isinstance(users, list)
    assert len(users) == 5
    for user in users:
        assert isinstance(user, User)

def test_update_user():
    """
    Test that an existing user can be updated.
    """
    updated_user_data = {
        "id": 2,  # ID of the user to update (jane_smith)
        "username": "jane.smith.updated",
        "email": "jane.updated@example.com",
        "password": "newpassword",
    }
    updated_user = User_Model.update(updated_user_data)

    # Fetch the user to verify the update
    user = User_Model.get(id=2)
    assert isinstance(user, User)
    assert user.username == "jane.smith.updated"
    assert user.email == "jane.updated@example.com"
    assert user.password == "newpassword"

def test_update_user_missing_id():
    """
    Test that update raises a ValueError if the user ID is missing.
    """
    updated_user_data = {
        "username": "jane.smith.updated",
        "email": "jane.updated@example.com",
        "password": "newpassword",
    }
    with pytest.raises(ValueError):
        User_Model.update(updated_user_data)

def test_update_nonexistent_user():
    """
    Test that update raises a ValueError if the user does not exist.
    """
    updated_user_data = {
        "id": 999,  # Non-existent user ID
        "username": "nonexistent_user",
        "email": "nonexistent@example.com",
        "password": "password",
    }
    with pytest.raises(ValueError):
        User_Model.update(updated_user_data)

def test_update_user_partial_data():
    """
    Test that update works correctly when only partial user data is provided.
    """
    updated_user_data = {
        "id": 4,  # ID of bob_williams
        "email": "bob.updated@example.com",  # Update only the email
    }
    updated_user = User_Model.update(updated_user_data)
    user = User_Model.get(id=4)
    assert user.email == "bob.updated@example.com"  # Email should be updated
    assert user.username == "bob_williams"  # Other fields should remain the same
    assert user.password == "password101"

def test_remove_user():
    """
    Test that a user can be removed successfully.
    """
    User_Model.remove(username="alice_johnson")
    assert not User_Model.exists(username="alice_johnson")
    # Check that the number of users is reduced by one.
    users = User_Model.get_all()
    assert len(users) == 4

def test_remove_nonexistent_user():
    """
    Test that remove raises a ValueError if the user does not exist.
    """
    with pytest.raises(ValueError):
        User_Model.remove(username="nonexistent_user")

