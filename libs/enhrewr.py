import telnetlib3
from libs.utils import User
from colored import Style, Fore
from typing import List, Optional
class KeyedOption:
    def __init__(self, key: str, desc: Optional[str], hidden: bool = False) -> None:
        self.key = key
        self.key_repr = KeyedOption.get_repr(key)
        self.desc = desc
        self.hidden = hidden

    @staticmethod
    def get_repr(key: str):
        return f"[{Style.bold}{key}{Style.reset}]"

    def __str__(self) -> str:
        return f"{self.key_repr} {self.desc}"


class TelnetController:
    def __init__(self, reader: telnetlib3.TelnetReader, writer: telnetlib3.TelnetWriter, user: Optional[User]) -> None:
        self.reader = reader
        self.writer = writer
        self.user = user

    async def prompt_text(self, prompt: str, echo: bool = True, max_len: int = 999999) -> str:
        """
            Prompts the user for text input with the selected prompt.
        """
        self.writer.write(f"\r\n{prompt} ")
        output = ""
        while True:
            inp = await self.reader.read(n=1)
            if inp == "\x0d": break
            if inp == "\x7f":
                output = output[:-1]
                if echo:
                    self.writer.write(f"\r{prompt} {output} ") ## clear inp
                    self.writer.write(f"\r{prompt} {output}")
                continue
            if len(output) == max_len:
                continue
            output += str(inp)
            if echo: self.writer.echo(inp)
        return output

    async def prompt_keylist(self, keys: List[KeyedOption], force: bool = True, return_output: bool = True) -> Optional[KeyedOption]:
        for key in keys:
            if not key.hidden: self.writer.write(f"\r\n{key}")
        self.writer.write(f"\r\n")
        while True:
            inp = await self.reader.read(n=1)
            matched = None
            for key in keys:
                if key.key == inp:
                    matched = key
                    break

            if matched:
                if return_output: self.writer.write(f"\r({matched.desc})                       ") # spaces to clear "must pick option"
                else: self.writer.write("\r                         \r")
                return matched

            if not force:
                self.writer.write("(no option selected)")
                return
            else:
                self.writer.write("\r(you must pick an option)")

    def newline(self) -> None:
        """
            Create a new line.
        """
        self.writer.write(f"\r\n")

    def write(self, string: str) -> None:
        """
            Writes a string to the writer.
        """
        self.writer.write(f"{string}")

    async def await_clear_writebuf(self) -> None:
        """
            Waits until the writing buffer is clear.
        """
        await self.writer.drain()

    def cls(self) -> None:
        """
            Clears the screen.
        """
        rows = self.writer.get_extra_info('rows')
        self.writer.write("\r\n" * rows)

    def write_title(self, title: str) -> None:
        """
            Writes a title to the screen.
        """
        self.writer.write(f"{Fore.royal_blue_1} ----= {Style.bold}{title}{Style.reset}{Fore.royal_blue_1} =----{Style.reset}")

    def close(self) -> None:
        self.writer.close()
