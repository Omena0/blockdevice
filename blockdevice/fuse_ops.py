"""
FUSE filesystem implementation for BlockDevice
"""

from __future__ import annotations

import errno
import os
import stat as _stat
import threading
from typing import Any

from fuse import FuseOSError, Operations


def _debug_print(*args: Any, **kwargs: Any) -> None:
    """Debug print that checks the parent module's debug flag"""
    try:
        import blockdevice

        if blockdevice.debug:  # type: ignore[attr-defined]
            print(*args, **kwargs)
    except (ImportError, AttributeError):
        # Silently fail if debug flag is not available
        pass


class BlockDeviceFUSE(Operations):
    """
    FUSE filesystem operations that delegate to BlockDevice callbacks.
    """

    def __init__(self, block_device: Any) -> None:
        self.block_device = block_device
        self.fd: int = 0
        self.open_files: dict[int, dict[str, Any]] = {}
        self.file_lock: threading.Lock = threading.Lock()

    def _get_next_fd(self) -> int:
        """Get next available file descriptor"""
        with self.file_lock:
            self.fd += 1
            return self.fd

    def _call_or_fallback(self, method_name: str, *args: Any, fallback: Any = None) -> Any:
        """Call a registered callback if available, otherwise use fallback."""
        call_method = f"call_{method_name}"
        if hasattr(self.block_device, call_method):
            try:
                result = getattr(self.block_device, call_method)(*args)
                if isinstance(result, bool) and not result:
                    raise FuseOSError(errno.EIO)
                return result
            except RuntimeError:
                # No callback registered - fall through to fallback
                pass
        return fallback

    def _bool_or_eio(self, result: Any, operation: str) -> None:
        """Raise EIO if result is a False bool. Return early if True bool."""
        if result is True:
            return
        if result is False:
            raise FuseOSError(errno.EIO)
        # Non-bool result (e.g. Mock in tests) - caller decides what to do

    def getattr(self, path: str, fh: int | None = None) -> dict[str, Any]:  # type: ignore[reportIncompatibleMethodOverride]
        """Get file attributes"""
        _debug_print(f"FUSE getattr: {path}")

        try:
            # If it's the root, always return directory attributes
            if path == "/":
                return {
                    "st_mode": _stat.S_IFDIR | 0o777,
                    "st_nlink": 2,
                    "st_size": 0,
                    "st_ctime": 0,
                    "st_mtime": 0,
                    "st_atime": 0,
                    "st_uid": os.getuid(),
                    "st_gid": os.getgid(),
                }

            # Try the STAT callback first for direct file/directory attributes
            if hasattr(self.block_device, "_call_stat"):
                try:
                    stat_result = self.block_device._call_stat(path)
                    if isinstance(stat_result, dict) and stat_result:
                        # Normalize high-level names (size, mode, modified, ...)
                        # to underlying st_* keys so plain dicts work too.
                        aliases = {
                            "size": "st_size",
                            "mode": "st_mode",
                            "modified": "st_mtime",
                            "mtime": "st_mtime",
                            "accessed": "st_atime",
                            "atime": "st_atime",
                            "created": "st_ctime",
                            "ctime": "st_ctime",
                            "owner": "st_uid",
                            "group": "st_gid",
                            "nlink": "st_nlink",
                            "inode": "st_ino",
                            "device": "st_dev",
                        }
                        normalized = {
                            aliases.get(k, k): v for k, v in stat_result.items()
                        }
                        attrs: dict[str, Any] = {  # type: ignore[assignment]
                            "st_mode": _stat.S_IFREG
                            | _stat.S_IRWXU
                            | _stat.S_IRWXG
                            | _stat.S_IRWXO,
                            "st_nlink": 1,
                            "st_size": 0,
                            "st_ctime": 0,
                            "st_mtime": 0,
                            "st_atime": 0,
                            "st_uid": os.getuid(),
                            "st_gid": os.getgid(),
                        } | normalized
                        # Convert high-level FileMode objects to raw ints for FUSE
                        for key in list(attrs):
                            val = attrs[key]
                            if hasattr(val, "__index__") and not isinstance(val, int):
                                attrs[key] = int(val)
                        return attrs
                except RuntimeError:
                    # No stat callback registered - fall through to listing
                    pass
                except Exception as e:  # noqa: BLE001 - defensive catch for FUSE stat callback
                    _debug_print(f"stat callback error for {path}: {e}")

            # Check if we can list the parent directory to see if this path exists
            parent_dir = os.path.dirname(path)
            if parent_dir is None:
                parent_dir = "/"
            filename = os.path.basename(path)

            if hasattr(self.block_device, "_call_list"):
                try:
                    contents = self.block_device._call_list(parent_dir)

                    file_exists = filename in contents
                    dir_exists = f"{filename}/" in contents

                    if dir_exists:
                        return {
                            "st_mode": _stat.S_IFDIR | 0o777,
                            "st_nlink": 2,
                            "st_size": 0,
                            "st_ctime": 0,
                            "st_mtime": 0,
                            "st_atime": 0,
                            "st_uid": os.getuid(),
                            "st_gid": os.getgid(),
                        }
                    elif file_exists:
                        # It's a file - try to get its size
                        try:
                            content = self.block_device._call_read(path)
                            size = (
                                len(content)
                                if isinstance(content, bytes)
                                else len(str(content).encode("utf-8"))
                            )
                        except (OSError, ValueError, TypeError):
                            size = 0

                        return {
                            "st_mode": _stat.S_IFREG | 0o666,
                            "st_nlink": 1,
                            "st_size": size,
                            "st_ctime": 0,
                            "st_mtime": 0,
                            "st_atime": 0,
                            "st_uid": os.getuid(),
                            "st_gid": os.getgid(),
                        }
                    else:
                        raise FuseOSError(errno.ENOENT)
                except OSError:
                    raise
                except Exception as e:  # noqa: BLE001 - defensive catch for FUSE parent dir check
                    _debug_print(
                        f"Error checking parent directory {parent_dir}: {e}"
                    )

            raise FuseOSError(errno.ENOENT)

        except FuseOSError:
            raise
        except Exception as e:
            _debug_print(f"getattr error for {path}: {e}")
            raise FuseOSError(errno.ENOENT) from e

    def readdir(self, path: str, fh: int | None) -> list[str]:  # type: ignore[reportIncompatibleMethodOverride]
        """Read directory contents"""
        _debug_print(f"FUSE readdir: {path}")

        dirents: list[str] = [".", ".."]

        try:
            contents: list[str] = self.block_device._call_list(path)
            for item in contents:
                if item.endswith("/"):
                    dirents.append(item[:-1])
                else:
                    dirents.append(item)
        except OSError:
            raise
        except Exception as e:  # noqa: BLE001 - defensive catch for FUSE readdir
            _debug_print(f"readdir error for {path}: {e}")

        return dirents

    def open(self, path: str, flags: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Open file"""
        _debug_print(f"FUSE open: {path}, flags: {flags} ({oct(flags)})")

        try:
            self.getattr(path)
        except FuseOSError as e:
            if e.errno != errno.ENOENT or not flags & os.O_CREAT:
                raise

            # File doesn't exist but O_CREAT is set, create it
            _debug_print(f"File {path} doesn't exist, creating it")
            self._bool_or_eio(
                self.block_device._call_write(path, b""), "open/create"
            )

        fd = self._get_next_fd()
        self.open_files[fd] = {"path": path, "flags": flags}
        _debug_print(f"Successfully opened {path} with fd: {fd}")
        return fd

    def read(self, path: str, length: int, offset: int, fh: int) -> bytes:  # type: ignore[reportIncompatibleMethodOverride]
        """Read file content"""
        _debug_print(f"FUSE read: {path}, length: {length}, offset: {offset}")

        try:
            content = self.block_device._call_read(path)
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            elif not isinstance(content, bytes):
                content_bytes = str(content).encode("utf-8")
            else:
                content_bytes = content

            return content_bytes[offset : offset + length]
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"read error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def write(self, path: str, buf: bytes, offset: int, fh: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Write to file"""
        _debug_print(f"FUSE write: {path}, offset: {offset}, length: {len(buf)}")

        try:
            if offset == 0:
                self._bool_or_eio(
                    self.block_device._call_write(path, buf), "write"
                )
            else:
                # For offset > 0, read existing content, modify, and write back
                try:
                    existing_content = self.block_device._call_read(path)
                    if isinstance(existing_content, str):
                        existing_content = existing_content.encode("utf-8")
                    elif not isinstance(existing_content, bytes):
                        existing_content = str(existing_content).encode("utf-8")
                except (OSError, ValueError, TypeError):
                    existing_content = b""

                if len(existing_content) < offset:
                    existing_content += b"\x00" * (offset - len(existing_content))

                new_content = (
                    existing_content[:offset]
                    + buf
                    + existing_content[offset + len(buf) :]
                )

                self._bool_or_eio(
                    self.block_device._call_write(path, new_content), "write"
                )
            return len(buf)
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"write error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def create(self, path: str, mode: int, fi: Any | None = None) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Create new file"""
        _debug_print(f"FUSE create: {path}, mode: {oct(mode)}")

        try:
            if hasattr(self.block_device, "_call_create"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_create(path, mode), "create"
                    )
                    fd = self._get_next_fd()
                    self.open_files[fd] = {
                        "path": path,
                        "flags": os.O_WRONLY | os.O_CREAT,
                        "mode": mode,
                    }
                    _debug_print(f"Successfully created file: {path} with fd: {fd}")
                    return fd
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: create empty file
            self._bool_or_eio(
                self.block_device._call_write(path, b""), "create"
            )
            fd = self._get_next_fd()
            self.open_files[fd] = {
                "path": path,
                "flags": os.O_WRONLY | os.O_CREAT,
                "mode": mode,
            }
            _debug_print(f"Successfully created file: {path} with fd: {fd}")
            return fd
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"create error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def mknod(self, path: str, mode: int, dev: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Create a file node - alternative to create"""
        _debug_print(f"FUSE mknod: {path}, mode: {oct(mode)}, dev: {dev}")

        try:
            if hasattr(self.block_device, "_call_mknod"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_mknod(path, mode, dev), "mknod"
                    )
                    _debug_print(f"Successfully created file node: {path}")
                    return 0
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: write empty content
            self._bool_or_eio(
                self.block_device._call_write(path, b""), "mknod"
            )
            _debug_print(f"Successfully created file node: {path}")
            return 0
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"mknod error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def truncate(self, path: str, length: int, fh: int | None = None) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        """Truncate file to specified length"""
        _debug_print(f"FUSE truncate: {path}, length: {length}")

        try:
            if hasattr(self.block_device, "_call_truncate"):
                try:
                    result = self.block_device._call_truncate(path, length)
                    if result is True:
                        return
                    if result is False:
                        raise FuseOSError(errno.EIO)
                    # Non-bool result - fall through to manual implementation
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: truncate/extend using read/write
            if length == 0:
                self._bool_or_eio(
                    self.block_device._call_write(path, b""), "truncate"
                )
            else:
                try:
                    existing_content = self.block_device._call_read(path)
                    if isinstance(existing_content, str):
                        existing_content = existing_content.encode("utf-8")
                    elif not isinstance(existing_content, bytes):
                        existing_content = str(existing_content).encode("utf-8")
                except (OSError, ValueError, TypeError):
                    existing_content = b""

                if len(existing_content) > length:
                    new_content = existing_content[:length]
                else:
                    new_content = existing_content + b"\x00" * (
                        length - len(existing_content)
                    )

                self._bool_or_eio(
                    self.block_device._call_write(path, new_content), "truncate"
                )
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"truncate error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def release(self, path: str, fh: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Release/close file"""
        _debug_print(f"FUSE release: {path}, fh: {fh}")

        with self.file_lock:
            self.open_files.pop(fh, None)
        return 0

    def lock(self, path: str, fh: int, cmd: int, lock: Any) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Handle file locking - required by Kate and other editors"""
        _debug_print(f"FUSE lock: {path}, fh: {fh}, cmd: {cmd}")
        return 0

    def flush(self, path: str, fh: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Flush file data - ensures data is written"""
        _debug_print(f"FUSE flush: {path}, fh: {fh}")
        return 0

    def fsync(self, path: str, datasync: bool, fh: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Sync file data to storage"""
        _debug_print(f"FUSE fsync: {path}, datasync: {datasync}, fh: {fh}")
        return 0

    def chmod(self, path: str, mode: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Change file permissions"""
        _debug_print(f"FUSE chmod: {path}, mode: {oct(mode)}")

        try:
            if hasattr(self.block_device, "_call_chmod"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_chmod(path, mode), "chmod"
                    )
                except RuntimeError:
                    pass
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"chmod error: {e}")
            raise FuseOSError(errno.EIO) from e
        return 0

    def chown(self, path: str, uid: int, gid: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Change file ownership"""
        _debug_print(f"FUSE chown: {path}, uid: {uid}, gid: {gid}")

        try:
            if hasattr(self.block_device, "_call_chown"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_chown(path, uid, gid), "chown"
                    )
                except RuntimeError:
                    pass
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"chown error: {e}")
            raise FuseOSError(errno.EIO) from e
        return 0

    def utimens(self, path: str, times: Any | None = None) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Update file timestamps"""
        _debug_print(f"FUSE utimens: {path}, times: {times}")

        try:
            if hasattr(self.block_device, "_call_utimens"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_utimens(path, times), "utimens"
                    )
                except RuntimeError:
                    pass
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"utimens error: {e}")
            raise FuseOSError(errno.EIO) from e
        return 0

    def access(self, path: str, mode: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Check file access permissions"""
        _debug_print(f"FUSE access: {path}, mode: {mode}")
        return 0

    def rename(self, old_path: str, new_path: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Rename/move a file or directory"""
        _debug_print(f"FUSE rename: {old_path} -> {new_path}")

        try:
            if hasattr(self.block_device, "_call_rename"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_rename(old_path, new_path), "rename"
                    )
                    _debug_print(
                        f"Successfully renamed: {old_path} -> {new_path}"
                    )
                    return 0
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: manual rename using read/write
            if not hasattr(self.block_device, "_call_read"):
                raise FuseOSError(errno.EROFS)

            try:
                content = self.block_device._call_read(old_path)
                self._bool_or_eio(
                    self.block_device._call_write(new_path, content), "rename"
                )
                self._remove_from_parent_directory(old_path)
                _debug_print(
                    f"Successfully renamed file: {old_path} -> {new_path}"
                )
                return 0
            except FileNotFoundError:
                # Maybe it's a directory
                if hasattr(self.block_device, "_call_list"):
                    try:
                        self.block_device._call_list(old_path)
                        self._bool_or_eio(
                            self.block_device._call_write(f"{new_path}/", b""),
                            "rename",
                        )
                        self._remove_from_parent_directory(old_path)
                        _debug_print(
                            f"Successfully renamed directory: {old_path} -> {new_path}"
                        )
                        return 0
                    except OSError:
                        raise
                    except Exception as exc:
                        raise FuseOSError(errno.ENOENT) from exc
                else:
                    raise FuseOSError(errno.ENOENT)
        except FuseOSError:
            raise
        except Exception as e:
            _debug_print(f"Rename error: {e}")
            raise FuseOSError(errno.EIO) from e

    def _remove_from_parent_directory(self, path: str) -> None:
        """Helper method to remove a file/directory from its parent directory listing"""
        parent = os.path.dirname(path) or "/"
        _debug_print(f"Removing {os.path.basename(path)} from parent {parent}")

    def unlink(self, path: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Delete a file"""
        _debug_print(f"FUSE unlink: {path}")

        try:
            if hasattr(self.block_device, "_call_delete"):
                self._bool_or_eio(self.block_device._call_delete(path), "unlink")
            else:
                self._remove_from_parent_directory(path)
            _debug_print(f"Successfully unlinked file: {path}")
            return 0
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"Unlink error: {e}")
            raise FuseOSError(errno.EIO) from e

    def rmdir(self, path: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Remove a directory"""
        _debug_print(f"FUSE rmdir: {path}")

        try:
            if hasattr(self.block_device, "_call_list"):
                contents = self.block_device._call_list(path)
                if contents and len(contents) > 0:
                    raise FuseOSError(errno.ENOTEMPTY)

            dir_path = path if path.endswith("/") else f"{path}/"

            if hasattr(self.block_device, "_call_delete"):
                self._bool_or_eio(
                    self.block_device._call_delete(dir_path), "rmdir"
                )
            else:
                self._remove_from_parent_directory(path)

            _debug_print(f"Successfully removed directory: {path}")
            return 0
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"Rmdir error: {e}")
            raise FuseOSError(errno.EIO) from e

    def mkdir(self, path: str, mode: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Create directory"""
        _debug_print(f"FUSE mkdir: {path}, mode: {oct(mode)}")

        try:
            if hasattr(self.block_device, "_call_mkdir"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_mkdir(path, mode), "mkdir"
                    )
                    _debug_print(f"Successfully created directory: {path}")
                    return 0
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: write empty content with trailing slash
            if not hasattr(self.block_device, "_call_list"):
                raise FuseOSError(errno.EROFS)

            parent = os.path.dirname(path) or "/"
            self.block_device._call_list(parent)
            self._bool_or_eio(
                self.block_device._call_write(f"{path}/", b""), "mkdir"
            )
            _debug_print(f"Successfully created directory: {path}")
            return 0
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"mkdir error for {path}: {e}")
            raise FuseOSError(errno.EIO) from e

    def statfs(self, path: str) -> dict[str, Any]:  # type: ignore[reportIncompatibleMethodOverride]
        """Get filesystem statistics"""
        _debug_print(f"FUSE statfs: {path}")

        return {
            "f_bsize": 10000000000,
            "f_frsize": 10000000000,
            "f_blocks": 10000000000000000000000000000000000000000000,
            "f_bfree": 10000000000000000000000000000000000000000000,
            "f_bavail": 10000000000000000000000000000000000000000000,
            "f_files": 10000000000000000000000000000000000000000000,
            "f_ffree": 10000000000000000000000000000000000000000000,
            "f_favail": 10000000000000000000000000000000000000000000,
            "f_flag": 0,
            "f_namemax": 255,
        }

    def init(self, conn: Any) -> int | None:  # type: ignore[reportIncompatibleMethodOverride]
        """Initialize filesystem"""
        _debug_print("FUSE init")
        return 0

    def destroy(self, conn: Any) -> None:  # type: ignore[reportIncompatibleMethodOverride]
        """Clean up filesystem"""
        _debug_print("FUSE destroy")

    def fsyncdir(self, path: str, datasync: bool, fh: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Sync directory contents"""
        _debug_print(f"FUSE fsyncdir: {path}, datasync: {datasync}, fh: {fh}")
        return 0

    def opendir(self, path: str, fi: Any) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Open directory"""
        _debug_print(f"FUSE opendir: {path}")
        return 0

    def releasedir(self, path: str, fi: Any) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Release directory"""
        _debug_print(f"FUSE releasedir: {path}")
        return 0

    def symlink(self, target: str, source: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Create symbolic link"""
        _debug_print(f"FUSE symlink: {target} -> {source}")

        try:
            if hasattr(self.block_device, "_call_symlink"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_symlink(target, source), "symlink"
                    )
                    _debug_print(
                        f"Successfully created symlink: {source} -> {target}"
                    )
                    return 0
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: write target as content
            self._bool_or_eio(
                self.block_device._call_write(source, target.encode("utf-8")),
                "symlink",
            )
            _debug_print(f"Successfully created symlink: {source} -> {target}")
            return 0
        except OSError:
            raise
        except Exception as e:
            _debug_print(f"Symlink error: {e}")
            raise FuseOSError(errno.EIO) from e

    def readlink(self, path: str) -> str:  # type: ignore[reportIncompatibleMethodOverride]
        """Read symbolic link target"""
        _debug_print(f"FUSE readlink: {path}")

        try:
            if not hasattr(self.block_device, "_call_read"):
                raise FuseOSError(errno.EROFS)
            content = self.block_device._call_read(path)
            if isinstance(content, str):
                return content
            return (
                content.decode("utf-8")
                if isinstance(content, bytes)
                else str(content)
            )
        except FuseOSError:
            raise
        except Exception as e:
            _debug_print(f"Readlink error: {e}")
            raise FuseOSError(errno.EIO) from e

    def link(self, target: str, source: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Create hard link"""
        _debug_print(f"FUSE link: {target} -> {source}")

        try:
            if hasattr(self.block_device, "_call_link"):
                try:
                    self._bool_or_eio(
                        self.block_device._call_link(target, source), "link"
                    )
                    _debug_print(
                        f"Successfully created hard link: {source} -> {target}"
                    )
                    return 0
                except RuntimeError:
                    # No callback registered - fall through to manual implementation
                    pass

            # Fallback: read target content, write to source
            if hasattr(self.block_device, "_call_read"):
                try:
                    content = self.block_device._call_read(target)
                    self._bool_or_eio(
                        self.block_device._call_write(source, content), "link"
                    )
                    _debug_print(
                        f"Successfully created hard link: {source} -> {target}"
                    )
                    return 0
                except FileNotFoundError:
                    raise FuseOSError(errno.ENOENT)
            else:
                raise FuseOSError(errno.EROFS)
        except FuseOSError:
            raise
        except Exception as e:
            _debug_print(f"Link error: {e}")
            raise FuseOSError(errno.EIO) from e

    def getxattr(self, path: str, name: str, position: int = 0) -> bytes:  # type: ignore[reportIncompatibleMethodOverride]
        """Get extended attribute"""
        _debug_print(f"FUSE getxattr: {path}, name: {name}")
        raise FuseOSError(errno.ENODATA)

    def setxattr(  # type: ignore[reportIncompatibleMethodOverride]
        self, path: str, name: str, value: bytes, options: int, position: int = 0
    ) -> int:
        """Set extended attribute"""
        _debug_print(f"FUSE setxattr: {path}, name: {name}")
        raise FuseOSError(errno.ENOTSUP)

    def listxattr(self, path: str) -> list[str]:  # type: ignore[reportIncompatibleMethodOverride]
        """List extended attributes"""
        _debug_print(f"FUSE listxattr: {path}")
        return []

    def removexattr(self, path: str, name: str) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Remove extended attribute"""
        _debug_print(f"FUSE removexattr: {path}, name: {name}")
        raise FuseOSError(errno.ENODATA)

    def ioctl(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        path: str,
        cmd: int,
        arg: int,
        fh: int,
        flags: int,
        in_data: bytes,
    ) -> int:
        """Handle ioctl operations"""
        _debug_print(f"FUSE ioctl: {path}, cmd: {cmd}, flags: {flags}")
        raise FuseOSError(errno.ENOTTY)

    def bmap(self, path: str, block: int, size: int) -> int:  # type: ignore[reportIncompatibleMethodOverride]
        """Map logical block to physical block"""
        _debug_print(f"FUSE bmap: {path}, block: {block}, size: {size}")
        raise FuseOSError(errno.EOPNOTSUPP)
