from colored import Style, Fore

class WhirlingDefinedException(Exception):
    pass

class UserException(WhirlingDefinedException):
    pass

class UserNotFoundException(UserException):
    pass

class UsernameInUseException(WhirlingDefinedException):
    pass

class User:
    def __init__(self, username, options) -> None:
        self.username = username
        self.options = options

    def __str__(self) -> str:
        return self.username

def whirlnet_textstyle(str):
    return f"{Fore.royal_blue_1}{str}{Style.reset}"
