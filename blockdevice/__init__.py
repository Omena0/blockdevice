"""
BlockDevice - A simple C++ Python library for block device operations

This module provides a BlockDevice class with decorators for read, write, and list operations.
It also includes FUSE filesystem support for mounting the block device as a real filesystem.
"""

from ._blockdevice import BlockDevice
from .fuse_ops import BlockDeviceFUSE
from .utils import Object, DiskObject, CompressedDiskObject, NetworkObject

debug = False

__version__ = "0.1.0"
__author__ = "Omena0"

__all__ = ["BlockDevice", "BlockDeviceFUSE", "Object", "DiskObject", "CompressedDiskObject", "NetworkObject"]

