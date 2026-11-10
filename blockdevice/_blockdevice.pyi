"""
Type stubs for BlockDevice C++ extension module
"""

import builtins
from typing import Any, Callable

from typing_extensions import TypeAlias, TypedDict

class StatResult(TypedDict, total=False):
    """Typed dict for file stat results with autocompletion for high-level keys."""

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


class BlockDevice:
    """
    BlockDevice class for creating virtual block devices with custom read/write/list operations.

    This class provides decorators (@bd.read, @bd.write, @bd.list) to register callback functions
    that handle filesystem operations when the device is mounted as a FUSE filesystem.
    """

    def __init__(
        self,
        mountpoint: str,
        dolphin: bool = False,
        name: str = ""
    ) -> None:
        """
        Initialize BlockDevice with mountpoint and optional parameters.

        Args:
            mountpoint: Path where the filesystem will be mounted
            dolphin: Whether to enable Dolphin file manager integration
            name: Display name for the device (defaults to mountpoint if empty)
        """

    @property
    def mountpoint(self) -> str:
        """Get the mountpoint path."""

    @property
    def name(self) -> str:
        """Get the display name."""

    @property
    def dolphin_integration(self) -> bool:
        """Get whether Dolphin integration is enabled."""

    # Decorator methods
    def read(self, func: Callable[[str], Any]) -> Callable[[str], Any]:
        """
        Decorator to register a read callback function.

        The decorated function should take a file path (str) and return the file content
        as bytes or string.

        Example:
            @bd.read
            def read_file(path: str) -> bytes:
                return b"file content"

        Args:
            func: Function that takes a path and returns file content

        Returns:
            The same function (for decorator chaining)
        """

    def write(self, func: Callable[[str, bytes], bool]) -> Callable[[str, bytes], bool]:
        """
        Decorator to register a write callback function.

        The decorated function should take a file path (str) and data (bytes),
        then return True if the write was successful, False otherwise.

        Example:
            @bd.write
            def write_file(path: str, data: bytes) -> bool:
                # Save data to path
                return True

        Args:
            func: Function that takes a path and data, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def list(self, func: Callable[[str], builtins.list[str]]) -> Callable[[str], builtins.list[str]]:
        """
        Decorator to register a directory listing callback function.

        The decorated function should take a directory path (str) and return
        a list of filenames/subdirectories in that directory.

        Example:
            @bd.list
            def list_directory(path: str) -> list[str]:
                return ["file1.txt", "subdir/"]

        Args:
            func: Function that takes a path and returns list of contents

        Returns:
            The same function (for decorator chaining)
        """

    def delete(self, func: Callable[[str], bool]) -> Callable[[str], bool]:
        """
        Decorator to register a delete callback function.

        The decorated function should take a file or directory path (str)
        and return True if the deletion was successful, False otherwise.

        Example:
            @bd.delete
            def delete_file(path: str) -> bool:
                # Delete file or directory at path
                return True

        Args:
            func: Function that takes a path and returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def stat(self, func: Callable[[str], dict[str, Any]]) -> Callable[[str], dict[str, Any]]:
        """
        Decorator to register a stat callback function.

        The decorated function should take a file or directory path (str)
        and return a :class:`StatResult` (or dict) of file attributes
        (e.g. st_mode, st_size, st_mtime, st_uid, st_gid) similar to
        :class:`os.stat_result`.

        Example:
            @bd.stat
            def stat_file(path: str) -> StatResult:
                return StatResult({
                    'st_mode': stat.S_IFREG | 0o644,
                    'st_size': 1024,
                })

        Args:
            func: Function that takes a path and returns a dict of attributes

        Returns:
            The same function (for decorator chaining)
        """

    def mkdir(self, func: Callable[[str, int], bool]) -> Callable[[str, int], bool]:
        """
        Decorator to register a mkdir callback function.

        The decorated function should take a directory path (str) and mode (int),
        and return True if the directory was created successfully.

        Example:
            @bd.mkdir
            def mkdir_dir(path: str, mode: int) -> bool:
                return True

        Args:
            func: Function that takes a path and mode, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def create(self, func: Callable[[str, int], bool]) -> Callable[[str, int], bool]:
        """
        Decorator to register a create (mkfile) callback function.

        The decorated function should take a file path (str) and mode (int),
        and return True if the file was created successfully.

        Example:
            @bd.create
            def create_file(path: str, mode: int) -> bool:
                return True

        Args:
            func: Function that takes a path and mode, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def mknod(self, func: Callable[[str, int, int], bool]) -> Callable[[str, int, int], bool]:
        """
        Decorator to register a mknod callback function.

        The decorated function should take a path (str), mode (int), and dev (int),
        and return True if the file node was created successfully.

        Args:
            func: Function that takes a path, mode, and dev, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def symlink(self, func: Callable[[str, str], bool]) -> Callable[[str, str], bool]:
        """
        Decorator to register a symlink callback function.

        The decorated function should take a target path (str) and source path (str),
        and return True if the symbolic link was created successfully.

        Example:
            @bd.symlink
            def make_symlink(target: str, source: str) -> bool:
                return True

        Args:
            func: Function that takes target and source paths, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def link(self, func: Callable[[str, str], bool]) -> Callable[[str, str], bool]:
        """
        Decorator to register a link (hard link) callback function.

        The decorated function should take a target path (str) and source path (str),
        and return True if the hard link was created successfully.

        Example:
            @bd.link
            def make_hard_link(target: str, source: str) -> bool:
                return True

        Args:
            func: Function that takes target and source paths, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def rename(self, func: Callable[[str, str], bool]) -> Callable[[str, str], bool]:
        """
        Decorator to register a rename callback function.

        The decorated function should take an old path (str) and new path (str),
        and return True if the rename was successful.

        Example:
            @bd.rename
            def rename_file(old_path: str, new_path: str) -> bool:
                return True

        Args:
            func: Function that takes old and new paths, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def truncate(self, func: Callable[[str, int], bool]) -> Callable[[str, int], bool]:
        """
        Decorator to register a truncate callback function.

        The decorated function should take a file path (str) and length (int),
        and return True if the file was truncated successfully.

        Example:
            @bd.truncate
            def truncate_file(path: str, length: int) -> bool:
                return True

        Args:
            func: Function that takes a path and length, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def chmod(self, func: Callable[[str, int], bool]) -> Callable[[str, int], bool]:
        """
        Decorator to register a chmod callback function.

        The decorated function should take a path (str) and mode (int),
        and return True if permissions were changed successfully.

        Example:
            @bd.chmod
            def change_perms(path: str, mode: int) -> bool:
                return True

        Args:
            func: Function that takes a path and mode, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def chown(self, func: Callable[[str, int, int], bool]) -> Callable[[str, int, int], bool]:
        """
        Decorator to register a chown callback function.

        The decorated function should take a path (str), uid (int), and gid (int),
        and return True if ownership was changed successfully.

        Example:
            @bd.chown
            def change_owner(path: str, uid: int, gid: int) -> bool:
                return True

        Args:
            func: Function that takes a path, uid, and gid, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    def utimens(self, func: Callable[[str, Any], bool]) -> Callable[[str, Any], bool]:
        """
        Decorator to register a utimens callback function.

        The decorated function should take a path (str) and times (tuple of atime/mtime),
        and return True if timestamps were updated successfully.

        Example:
            @bd.utimens
            def update_times(path: str, times: tuple) -> bool:
                return True

        Args:
            func: Function that takes a path and times, returns success boolean

        Returns:
            The same function (for decorator chaining)
        """

    # Internal callback invocation (used by FUSE operations; callbacks are
    # registered via the decorators above, which are the high-level API)
    def _call_read(self, path: str) -> Any:
        """Call the registered read callback with the given path."""

    def _call_write(self, path: str, data: Any) -> bool:
        """Call the registered write callback with the given path and data."""

    def _call_list(self, path: str) -> builtins.list[str]:
        """Call the registered list callback with the given path."""

    def _call_delete(self, path: str) -> bool:
        """Call the registered delete callback with the given path."""

    def _call_stat(self, path: str) -> dict[str, Any]:
        """Call the registered stat callback with the given path."""

    def _call_mkdir(self, path: str, mode: int) -> bool:
        """Call the registered mkdir callback with the given path and mode."""

    def _call_create(self, path: str, mode: int) -> bool:
        """Call the registered create callback with the given path and mode."""

    def _call_mknod(self, path: str, mode: int, dev: int) -> bool:
        """Call the registered mknod callback with the given path, mode, and dev."""

    def _call_symlink(self, target: str, source: str) -> bool:
        """Call the registered symlink callback with the given target and source."""

    def _call_link(self, target: str, source: str) -> bool:
        """Call the registered link callback with the given target and source."""

    def _call_rename(self, old_path: str, new_path: str) -> bool:
        """Call the registered rename callback with the given old and new paths."""

    def _call_truncate(self, path: str, length: int) -> bool:
        """Call the registered truncate callback with the given path and length."""

    def _call_chmod(self, path: str, mode: int) -> bool:
        """Call the registered chmod callback with the given path and mode."""

    def _call_chown(self, path: str, uid: int, gid: int) -> bool:
        """Call the registered chown callback with the given path, uid, and gid."""

    def _call_utimens(self, path: str, times: Any) -> bool:
        """Call the registered utimens callback with the given path and times."""

    # FUSE filesystem lifecycle. start()/stop() are the public high-level API;
    # _mount()/_unmount() are the low-level mounting primitives.
    def _mount(self) -> None:
        """Mount the filesystem at the specified mountpoint (internal)."""

    def _unmount(self) -> None:
        """Unmount the filesystem (internal)."""

    def start(self, foreground: bool = True) -> None:
        """Start the FUSE filesystem."""

    def stop(self) -> None:
        """Stop the FUSE filesystem."""

    def is_mounted(self) -> bool:
        """Check if the filesystem is currently mounted."""
