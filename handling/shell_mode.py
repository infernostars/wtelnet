import asyncio, uuid
import shlex
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from libs.enhrewr import TelnetController, KeyedOption, User

class Command(ABC):
    @abstractmethod
    async def execute(self, args: List[str], ctx: TelnetController):
        pass

    @property
    @abstractmethod
    def help(self) -> str:
        pass

class Echo(Command):
    async def execute(self, args: List[str], ctx: TelnetController):
        ctx.newline()
        ctx.write(' '.join(args))

    @property
    def help(self):
        return "Echo the given arguments"

class Exit(Command):
    async def execute(self, args: List[str], ctx: TelnetController):
        ctx.newline()
        ctx.write("Goodbye!")
        ctx.newline()
        await ctx.await_clear_writebuf()
        ctx.close()

    @property
    def help(self):
        return "Exit the shell"

class Help(Command):
    def __init__(self, shell):
        self.shell = shell

    async def execute(self, args: List[str], ctx: TelnetController):
        ctx.newline()
        ctx.write_title("Available Commands")
        ctx.newline()
        for cmd, command in self.shell.commands.items():
            ctx.write(f"  {cmd}: {command.help}")
            ctx.newline()

    @property
    def help(self):
        return "Display this help message"

class SendMessage(Command):
    def __init__(self, shell_manager):
        self.shell_manager = shell_manager

    async def execute(self, args: List[str], ctx: TelnetController):
        if len(args) < 2:
            ctx.newline()
            ctx.write("Usage: send <username> <message>")
            return

        target_username = args[0]
        message = args[1]

        for shell in self.shell_manager.shells.values():
            if shell.user.username == target_username:
                await shell.send_message(f"Message from {ctx.user.username}: {message}")
                ctx.newline()
                ctx.write(f"Message sent to {target_username}")
                return
        ctx.newline()
        ctx.write(f"User {target_username} not found")

    @property
    def help(self):
        return "Send a message to a specific user"

class BroadcastMessage(Command):
    def __init__(self, shell_manager):
        self.shell_manager = shell_manager

    async def execute(self, args: List[str], ctx: TelnetController):
        if not args:
            ctx.newline()
            ctx.write("Usage: broadcast <message>")
            return

        message = args[0]
        await self.shell_manager.broadcast_message(f"Broadcast from {ctx.user.username}: {message}")
        ctx.newline()
        ctx.write("Message broadcasted to all users")

    @property
    def help(self):
        return "Broadcast a message to all users"

class UserList(Command):
    def __init__(self, shell_manager):
        self.shell_manager = shell_manager

    async def execute(self, args: List[str], ctx: TelnetController):
        users = [shell.user.username for shell in self.shell_manager.shells.values()]
        users.sort()  # Sort the usernames alphabetically

        ctx.newline()
        ctx.write_title("Active Users")
        ctx.newline()
        for username in users:
            ctx.write(f"- {username}")
            ctx.newline()

    @property
    def help(self):
        return "List all active users"

class WhirlShell:
    def __init__(self, ctx: TelnetController):
        self.commands = {}
        self.ctx = ctx
        self.message_queue = asyncio.Queue()
        self.running = False
        self.shell_id = str(uuid.uuid4())  # Generate a unique ID
        self.user = ctx.user  # Store the user associated with this shell

    def add_command(self, name: str, command: Command):
        self.commands[name.lower()] = command

    async def run(self):
        self.ctx.write("welcome to whirlshell! type `help' for available commands.")
        self.ctx.newline()
        self.ctx.write("use \"quotes\" for arguments with spaces.")
        self.ctx.newline()

        self.running = True
        while self.running:
            command = await self.ctx.prompt_text("wsh>")
            await self.execute(command)

            # Process any messages in the queue
            while not self.message_queue.empty():
                message = await self.message_queue.get()
                self.ctx.newline()
                self.ctx.write(f"Message received: {message}")
                self.ctx.newline()

    async def execute(self, command: str):
        try:
            args = shlex.split(command)  # This handles quoted arguments correctly
        except ValueError as e:
            self.ctx.write(f"Error parsing command: {str(e)}")
            self.ctx.newline()
            return

        if not args:
            return

        cmd = args[0].lower()
        if cmd in self.commands:
            await self.commands[cmd].execute(args[1:], self.ctx)
        else:
            self.ctx.write(f"Unknown command: {cmd}")
            self.ctx.newline()
    async def send_message(self, message: str):
        await self.message_queue.put(message)
        if not self.running:
            # If the shell is not running, process the message immediately
            await self.process_messages()

    async def process_messages(self):
        while not self.message_queue.empty():
            message = await self.message_queue.get()
            self.ctx.write(f"{message}")

    def stop(self):
        self.running = False

class ShellManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ShellManager, cls).__new__(cls)
            cls._instance.shells: Dict[str, WhirlShell] = {}
            cls._instance.user_shell_map: Dict[str, str] = {}  # Map usernames to shell IDs
        return cls._instance

    async def create_shell(self, ctx: TelnetController) -> WhirlShell:
        """
        Creates and initializes a WhirlShell instance with the given TelnetController.
        """
        shell = WhirlShell(ctx)

        # Add default commands
        shell.add_command("echo", Echo())
        shell.add_command("exit", Exit())
        shell.add_command("help", Help(shell))
        shell.add_command("send", SendMessage(self))
        shell.add_command("broadcast", BroadcastMessage(self))
        shell.add_command("users", UserList(self))

        self.shells[shell.shell_id] = shell
        self.user_shell_map[shell.user.username] = shell.shell_id
        return shell

    async def broadcast_message(self, message: str):
        """
        Sends a message to all active shells.
        """
        for shell in self.shells.values():
            await shell.send_message(message)

    def get_shell(self, shell_id: str) -> Optional[WhirlShell]:
        """
        Retrieves a shell by its ID.
        """
        return self.shells.get(shell_id)

    def get_shell_by_user(self, user: User) -> Optional[WhirlShell]:
        """
        Retrieves a shell by its associated user.
        Returns None if no shell is found for the user.
        """
        shell_id = self.user_shell_map.get(user.username)
        return self.shells.get(shell_id) if shell_id else None

    def remove_shell(self, shell_id: str):
        """
        Removes a shell from the manager.
        """
        if shell_id in self.shells:
            shell = self.shells[shell_id]
            del self.shells[shell_id]
            del self.user_shell_map[shell.user.username]

    def get_all_shell_ids(self) -> List[str]:
        """
        Returns a list of all shell IDs.
        """
        return list(self.shells.keys())
