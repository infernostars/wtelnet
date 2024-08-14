import asyncio
import telnetlib3
import shlex
from tinydb import TinyDB, Query
import hashlib
import os, logging

from libs.enhrewr import TelnetController
from handling.telnet_handler import entry
# Initialize TinyDB
db = TinyDB('users.json')

async def shellentry(reader, writer):
    await entry(TelnetController(reader, writer, None))

async def main():
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='wtelnet.log', level=logging.DEBUG)
    server = await telnetlib3.create_server(port=25565, shell=shellentry)
    print(f'Telnet server started on port 25565')
    await server.wait_closed()

if __name__ == '__main__':
    asyncio.run(main())
