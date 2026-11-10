import socket

from blockdevice import *

dev = BlockDevice("/mnt/http", name="Http")

type Address = tuple[str, int]
conns: dict[Address, list[socket.socket]] = {}

@dev.write
def fs_write(path: str, data: bytes):
    return True

dev.start(True)
