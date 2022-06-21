"""Poor man's authentication."""
import binascii
import hashlib
import os
from dataclasses import dataclass
from typing import Dict

AUTH_HASH_ALG = "sha512"
AUTH_PBKDF_ITERATIONS = 100000


@dataclass
class User:
    username: str
    password_hash: str


# see https://www.vitoshacademy.com/hashing-passwords-in-python/
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode("ascii")
    pwdhash = hashlib.pbkdf2_hmac(
        AUTH_HASH_ALG, password.encode("utf-8"), salt, AUTH_PBKDF_ITERATIONS
    )
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode("ascii")


def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac(
        AUTH_HASH_ALG,
        provided_password.encode("utf-8"),
        salt.encode("ascii"),
        AUTH_PBKDF_ITERATIONS,
    )
    pwdhash = binascii.hexlify(pwdhash).decode("ascii")
    return pwdhash == stored_password


# store this in a DB in real life
poor_mans_user_store: Dict[str, User] = {
    "user1": User(username="user1", password_hash=hash_password("user1")),
    "user2": User(username="user1", password_hash=hash_password("user2")),
}


def get_user(username):
    # this would be a database query in real life
    if username not in poor_mans_user_store:
        return None
    return poor_mans_user_store[username]


def authenticate(username, password):
    user = get_user(username)
    if not user:
        return False
    return verify_password(user.password_hash, password)


class SessionAuthenticator:
    session_username_key = "username"

    def __init__(self, app, session):
        self.app = app
        self.session = session
        self.change_handlers = []

    def authenticate(self, username, password):
        """Authenticate a session via username and password."""
        authenticated = authenticate(username=username, password=password)
        if authenticated:
            self.session.values[self.session_username_key] = username
            self.on_change(True)
        return authenticated

    def logout(self):
        """De-authenticate a session by removing the username from the session data."""
        del self.session.values[self.session_username_key]
        self.on_change(False)

    def is_authenticated(self):
        return self.session_username_key in self.session.values

    def get_user(self):
        if self.session_username_key in self.session.values:
            return self.session.values[self.session_username_key]
        return None

    def register_handler(self, handler):
        self.change_handlers.append(handler)

    def on_change(self, authenticated):
        [self.app.add_task(handler(authenticated)) for handler in self.change_handlers]
