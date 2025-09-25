"""
BlockDevice - A simple C++ Python library for block device operations

This module provides a BlockDevice class with decorators for read, write, and list operations.
It also includes FUSE filesystem support for mounting the block device as a real filesystem.
"""

from typing import TYPE_CHECKING

# Debug flag - set to True to enable debug output
debug = False

if TYPE_CHECKING:
    from ._blockdevice import BlockDevice as _BlockDevice
    BlockDevice = _BlockDevice
else:
    from ._blockdevice import BlockDevice

from .fuse_ops import BlockDeviceFUSE
from .utils import *

__version__ = "0.1.0"
__author__ = "Omena0"

__all__ = ["BlockDevice", "BlockDeviceFUSE", "Object", "DiskObject", "CompressedDiskObject", "NetworkObject"]

