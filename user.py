from typing import Dict
import libs.utils, tinydb, hashlib
userdb = tinydb.TinyDB("./users.json")

def register_user(username: str, password: str) -> None:
    user = tinydb.Query
    search = userdb.search(tinydb.where("username") == username)
    if len(search) > 0:
        raise libs.utils.UsernameInUseException()
    hash = hashlib.blake2b(password.encode())
    userdb.insert({'username': username, 'phash': hash.hexdigest(), 'opts': {}})

def login(username: str, password: str) -> libs.utils.User:
    hash = hashlib.blake2b(password.encode())
    try:
        search = userdb.search((tinydb.where("username") == username) & (tinydb.where("phash") == hash.hexdigest()))
        return libs.utils.User(search[0]["username"], search[0]["opts"])
    except Exception as e:
        raise libs.utils.UserNotFoundException()

def get_user_opts(username: str) -> Dict:
    try:
        search = userdb.search((tinydb.where("username") == username))
        return search[0]["opts"]
    except Exception as e:
        raise libs.utils.UserNotFoundException()
