"""
BlockDevice - A simple C++ Python library for block device operations

This module provides a BlockDevice class with decorators for read, write, list, stat, and delete operations.
It also includes FUSE filesystem support for mounting the block device as a real filesystem.
"""

from __future__ import annotations

import stat as _stat
from typing import Any, ClassVar

from ._blockdevice import BlockDevice
from .utils import CompressedDiskObject, DiskObject, NetworkObject, Object

debug = False

__version__ = "0.1.0"
__author__ = "Omena0"


class FileMode(int):
    """High-level file mode for ``st_mode``. Hides FUSE/stat bitmasks.

    Build a file mode with readable arguments instead of raw bitwise flags::

        @bd.stat
        def stat_file(path: str) -> StatResult:
            return StatResult({
                "st_mode": FileMode(type="file", owner="rwx", group="r--", other="r--"),
                "st_size": 1024,
            })

    The object *is* an ``int``, so it works directly as ``st_mode`` and in
    bitwise expressions (``|``, ``&``) without any conversion.

    Args:
        type: One of ``"file"``, ``"dir"``, ``"link"``, ``"socket"``,
            ``"block"``, ``"char"``, ``"fifo"``. Defaults to ``"file"``.
        owner: Permission string for the owner, e.g. ``"rwx"``, ``"r--"``,
            ``"--x"``. Defaults to ``"rwx"``.
        group: Permission string for the group. Defaults to ``"r--"``.
        other: Permission string for others. Defaults to ``"r--"``.
        setuid: Set the setuid bit.
        setgid: Set the setgid bit.
        sticky: Set the sticky bit.
    """

    _TYPES: ClassVar[dict[str, int]] = {
        "file": _stat.S_IFREG,
        "dir": _stat.S_IFDIR,
        "link": _stat.S_IFLNK,
        "socket": _stat.S_IFSOCK,
        "block": _stat.S_IFBLK,
        "char": _stat.S_IFCHR,
        "fifo": _stat.S_IFIFO,
    }

    def __new__(
        cls,
        *,
        type: str = "file",
        owner: str = "rwx",
        group: str = "r--",
        other: str = "r--",
        setuid: bool = False,
        setgid: bool = False,
        sticky: bool = False,
    ):
        if type not in cls._TYPES:
            raise ValueError(
                f"Invalid file type: {type!r}. Valid types: {sorted(cls._TYPES)}"
            )
        for name, value in (("owner", owner), ("group", group), ("other", other)):
            if not all(c in "rwx-" for c in value) or len(value) > 3:
                raise ValueError(
                    f"Invalid {name} permissions: {value!r}. Use 'r', 'w', 'x', '-'."
                )
        mode = cls._TYPES[type]
        mode |= cls._perm_value(owner) << 6
        mode |= cls._perm_value(group) << 3
        mode |= cls._perm_value(other) << 0
        if setuid:
            mode |= _stat.S_ISUID
        if setgid:
            mode |= _stat.S_ISGID
        if sticky:
            mode |= _stat.S_ISVTX
        return super().__new__(cls, mode)

    def __init__(
        self,
        *,
        type: str = "file",
        owner: str = "rwx",
        group: str = "r--",
        other: str = "r--",
        setuid: bool = False,
        setgid: bool = False,
        sticky: bool = False,
    ) -> None:
        self.type = type
        self.owner = owner
        self.group = group
        self.other = other
        self.setuid = setuid
        self.setgid = setgid
        self.sticky = sticky

    @staticmethod
    def _perm_value(perm: str) -> int:
        val = 0
        if "r" in perm:
            val |= 4
        if "w" in perm:
            val |= 2
        if "x" in perm:
            val |= 1
        return val

    def __repr__(self) -> str:
        return (
            f"FileMode(type={self.type!r}, owner={self.owner!r}, "
            f"group={self.group!r}, other={self.other!r}, "
            f"setuid={self.setuid}, setgid={self.setgid}, sticky={self.sticky})"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FileMode):
            return int(self) == int(other)
        return NotImplemented

    def __hash__(self) -> int:
        return hash(int(self))


class StatResult(dict):
    """A validated, high-level dict for file stat results.

    Uses readable argument names directly, with no aliases or mapping::

        @bd.stat
        def stat_file(path: str) -> StatResult:
            return StatResult(
                size=1024,
                mode=FileMode(type="file", owner="rwx", group="r--", other="r--"),
                modified=1234567890.0,
            )

    Valid keys: size, mode, modified, accessed, created, owner, group,
    nlink, inode, device.

    Provides attribute access (``result.size``) in addition to dictionary
    access (``result["size"]``).
    """

    size: int
    mode: int
    modified: float
    accessed: float
    created: float
    owner: int
    group: int
    nlink: int
    inode: int
    device: int

    _VALID_KEYS = frozenset({
        "size", "mode", "modified", "accessed", "created",
        "owner", "group", "nlink", "inode", "device",
    })

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._validate()

    def __setitem__(self, key: str, value: Any) -> None:
        if key not in self._VALID_KEYS:
            raise KeyError(
                f"Invalid stat key: {key!r}. Valid keys: {sorted(self._VALID_KEYS)}"
            )
        super().__setitem__(key, value)

    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(key)

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute {name!r}"
            ) from None

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
            return
        if name not in self._VALID_KEYS:
            raise AttributeError(f"Invalid stat attribute: {name!r}")
        self[name] = value

    def _validate(self) -> None:
        for key in self:
            if key not in self._VALID_KEYS:
                raise KeyError(
                    f"Invalid stat key: {key!r}. Valid keys: {sorted(self._VALID_KEYS)}"
                )

    def update(self, *args: Any, **kwargs: Any) -> None:
        for k, v in dict(*args, **kwargs).items():
            self[k] = v

    def setdefault(self, key: str, default: Any = None) -> Any:
        if key not in self._VALID_KEYS:
            raise KeyError(f"Invalid stat key: {key!r}")
        return super().setdefault(key, default)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({super().__repr__()})"


__all__ = [
    "BlockDevice",
    "CompressedDiskObject",
    "DiskObject",
    "FileMode",
    "NetworkObject",
    "Object",
    "StatResult",
]
