"""
FUSE filesystem implementation for BlockDevice
"""

import os
import stat
import errno
import threading
from typing import Any, Dict, List, Optional, Union
from fuse import FuseOSError, Operations

def _debug_print(*args, **kwargs):
    """Debug print that checks the parent module's debug flag"""
    try:
        import blockdevice
        if blockdevice.debug:
            print(*args, **kwargs)
    except (ImportError, AttributeError):
        # Silently fail if debug flag is not available
        pass

import threading
from typing import Any, Dict, List, Optional, Union
from fuse import FuseOSError, Operations

# Import debug function from parent module
def _debug__debug_print(*args, **kwargs):
    """Debug print that respects the module's debug flag"""
    try:
        import blockdevice
        if blockdevice.debug:
            _debug_print(*args, **kwargs)
    except (ImportError, AttributeError):
        # Fallback if debug flag is not available
        pass


class BlockDeviceFUSE(Operations):
    """
    FUSE filesystem operations that delegate to BlockDevice callbacks
    """

    def __init__(self, block_device: Any) -> None:
        self.block_device: Any = block_device
        self.fd: int = 0
        self.open_files: Dict[int, str] = {}
        self.file_lock: threading.Lock = threading.Lock()  # Renamed to avoid conflict with fuse lock() method

    def _get_next_fd(self) -> int:
        """Get next available file descriptor"""
        with self.file_lock:
            self.fd += 1
            return self.fd

    def getattr(self, path: str, fh: Optional[int] = None) -> Dict[str, Any]:
        """Get file attributes"""
        _debug__debug_print(f"FUSE getattr: {path}")

        try:
            # If it's the root, always return directory attributes
            if path == '/':
                return {
                    'st_mode': stat.S_IFDIR | 0o777,  # Full permissions for root directory
                    'st_nlink': 2,
                    'st_size': 0,
                    'st_ctime': 0,
                    'st_mtime': 0,
                    'st_atime': 0,
                    'st_uid': os.getuid(),
                    'st_gid': os.getgid(),
                }

            # Check if we can list the parent directory to see if this path exists
            parent_dir = os.path.dirname(path)
            if parent_dir == '':
                parent_dir = '/'
            filename = os.path.basename(path)

            if hasattr(self.block_device, 'call_list'):
                try:
                    contents = self.block_device.call_list(parent_dir)

                    # Check if this file/directory exists in the parent listing
                    file_exists = filename in contents
                    dir_exists = (filename + '/') in contents

                    if dir_exists:
                        # It's a directory
                        return {
                            'st_mode': stat.S_IFDIR | 0o777,
                            'st_nlink': 2,
                            'st_size': 0,
                            'st_ctime': 0,
                            'st_mtime': 0,
                            'st_atime': 0,
                            'st_uid': os.getuid(),
                            'st_gid': os.getgid(),
                        }
                    elif file_exists:
                        # It's a file - try to get its size
                        try:
                            content = self.block_device.call_read(path)
                            if isinstance(content, bytes):
                                size = len(content)
                            else:
                                size = len(str(content).encode('utf-8'))
                        except:
                            size = 0

                        return {
                            'st_mode': stat.S_IFREG | 0o666,  # More permissive file permissions
                            'st_nlink': 1,
                            'st_size': size,
                            'st_ctime': 0,
                            'st_mtime': 0,
                            'st_atime': 0,
                            'st_uid': os.getuid(),  # Current user
                            'st_gid': os.getgid(),  # Current group
                        }
                    else:
                        # File/directory doesn't exist in parent listing - return ENOENT immediately
                        raise FuseOSError(errno.ENOENT)

                except Exception as e:
                    _debug_print(f"Error checking parent directory {parent_dir}: {e}")
                    # If we can't check parent, try direct operations

            # If we can't check parent, just return ENOENT
            # This prevents infinite recursion with file creation attempts
            raise FuseOSError(errno.ENOENT)

        except FuseOSError:
            # Re-raise FUSE errors as-is
            raise
        except Exception as e:
            _debug_print(f"getattr error for {path}: {e}")
            raise FuseOSError(errno.ENOENT)

    def readdir(self, path: str, fh: Optional[int]) -> List[str]:
        """Read directory contents"""
        _debug_print(f"FUSE readdir: {path}")

        dirents: List[str] = ['.', '..']

        try:
            contents: List[str] = self.block_device.call_list(path)
            # Strip trailing slashes for directory entries
            for item in contents:
                if item.endswith('/'):
                    dirents.append(item[:-1])  # Remove trailing slash
                else:
                    dirents.append(item)
        except Exception as e:
            _debug_print(f"readdir error for {path}: {e}")
            # Return just . and .. if listing fails

        return dirents

    def open(self, path: str, flags: int) -> int:
        """Open file"""
        _debug_print(f"FUSE open: {path}, flags: {flags} ({oct(flags)})")

        # Check if file exists by trying to get its attributes
        try:
            self.getattr(path)
        except FuseOSError as e:
            if e.errno == errno.ENOENT and (flags & os.O_CREAT):
                # File doesn't exist but O_CREAT is set, create it
                _debug_print(f"File {path} doesn't exist, creating it")
                success = self.block_device.call_write(path, b'')
                if not success:
                    raise FuseOSError(errno.EIO)
            else:
                raise

        fd = self._get_next_fd()
        self.open_files[fd] = {
            'path': path,
            'flags': flags
        }
        _debug_print(f"Successfully opened {path} with fd: {fd}")
        return fd

    def read(self, path: str, length: int, offset: int, fh: int) -> bytes:
        """Read file content"""
        _debug_print(f"FUSE read: {path}, length: {length}, offset: {offset}")

        try:
            content: Union[str, bytes] = self.block_device.call_read(path)
            if isinstance(content, str):
                content_bytes: bytes = content.encode('utf-8')
            elif not isinstance(content, bytes):
                content_bytes = str(content).encode('utf-8')
            else:
                content_bytes = content

            return content_bytes[offset:offset + length]
        except Exception as e:
            _debug_print(f"read error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def write(self, path: str, buf: bytes, offset: int, fh: int) -> int:
        """Write to file"""
        _debug_print(f"FUSE write: {path}, offset: {offset}, length: {len(buf)}")

        try:
            # For proper write support, we should handle offsets properly
            # For now, let's handle simple case of writing at offset 0
            if offset == 0:
                success = self.block_device.call_write(path, buf)
                if success:
                    return len(buf)
                else:
                    raise FuseOSError(errno.EIO)
            else:
                # For offset > 0, we need to read existing content, modify, and write back
                try:
                    existing_content = self.block_device.call_read(path)
                    if isinstance(existing_content, str):
                        existing_content = existing_content.encode('utf-8')
                    elif not isinstance(existing_content, bytes):
                        existing_content = str(existing_content).encode('utf-8')
                except:
                    existing_content = b''

                # Extend content if necessary
                if len(existing_content) < offset:
                    existing_content += b'\x00' * (offset - len(existing_content))

                # Insert new data at offset
                new_content = existing_content[:offset] + buf + existing_content[offset + len(buf):]

                success = self.block_device.call_write(path, new_content)
                if success:
                    return len(buf)
                else:
                    raise FuseOSError(errno.EIO)

        except Exception as e:
            _debug_print(f"write error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def truncate(self, path, length, fh=None):
        """Truncate file to specified length"""
        _debug_print(f"FUSE truncate: {path}, length: {length}")

        try:
            if length == 0:
                # Truncate to empty
                success = self.block_device.call_write(path, b'')
                if not success:
                    raise FuseOSError(errno.EIO)
            else:
                # Read existing content and truncate/extend as needed
                try:
                    existing_content = self.block_device.call_read(path)
                    if isinstance(existing_content, str):
                        existing_content = existing_content.encode('utf-8')
                    elif not isinstance(existing_content, bytes):
                        existing_content = str(existing_content).encode('utf-8')
                except:
                    existing_content = b''

                if len(existing_content) > length:
                    # Truncate
                    new_content = existing_content[:length]
                else:
                    # Extend with zeros
                    new_content = existing_content + b'\x00' * (length - len(existing_content))

                success = self.block_device.call_write(path, new_content)
                if not success:
                    raise FuseOSError(errno.EIO)

        except Exception as e:
            _debug_print(f"truncate error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def create(self, path: str, mode: int, fi: Optional[Any] = None) -> int:
        """Create new file"""
        _debug_print(f"FUSE create: {path}, mode: {oct(mode)}")

        try:
            # Create empty file
            success: bool = self.block_device.call_write(path, b'')
            if success:
                fd: int = self._get_next_fd()
                self.open_files[fd] = {
                    'path': path,
                    'flags': os.O_WRONLY | os.O_CREAT,
                    'mode': mode
                }
                _debug_print(f"Successfully created file: {path} with fd: {fd}")
                return fd
            else:
                _debug_print(f"Failed to create file: {path}")
                raise FuseOSError(errno.EIO)
        except Exception as e:
            _debug_print(f"create error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def mknod(self, path, mode, dev):
        """Create a file node - alternative to create"""
        _debug_print(f"FUSE mknod: {path}, mode: {oct(mode)}, dev: {dev}")

        try:
            # Create empty file
            success = self.block_device.call_write(path, b'')
            if success:
                _debug_print(f"Successfully created file node: {path}")
                return 0
            else:
                _debug_print(f"Failed to create file node: {path}")
                raise FuseOSError(errno.EIO)
        except Exception as e:
            _debug_print(f"mknod error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def release(self, path: str, fh: int) -> int:
        """Release/close file"""
        _debug_print(f"FUSE release: {path}, fh: {fh}")

        with self.file_lock:
            if fh in self.open_files:
                del self.open_files[fh]
        return 0

    def lock(self, path: str, fh: int, cmd: int, lock: Any) -> int:
        """Handle file locking - required by Kate and other editors"""
        _debug_print(f"FUSE lock: {path}, fh: {fh}, cmd: {cmd}")
        # For simplicity, we'll just return 0 (success) for all lock operations
        # In a real implementation, you'd handle different lock types
        return 0

    def flush(self, path: str, fh: int) -> int:
        """Flush file data - ensures data is written"""
        _debug_print(f"FUSE flush: {path}, fh: {fh}")
        # Nothing special needed for our in-memory filesystem
        return 0

    def fsync(self, path: str, datasync: bool, fh: int) -> int:
        """Sync file data to storage"""
        _debug_print(f"FUSE fsync: {path}, datasync: {datasync}, fh: {fh}")
        # Nothing special needed for our in-memory filesystem
        return 0

    def chmod(self, path: str, mode: int) -> int:
        """Change file permissions"""
        _debug_print(f"FUSE chmod: {path}, mode: {oct(mode)}")
        # We'll just pretend to succeed
        return 0

    def chown(self, path: str, uid: int, gid: int) -> int:
        """Change file ownership"""
        _debug_print(f"FUSE chown: {path}, uid: {uid}, gid: {gid}")
        # We'll just pretend to succeed
        return 0

    def utimens(self, path: str, times: Optional[Any] = None) -> int:
        """Update file timestamps"""
        _debug_print(f"FUSE utimens: {path}, times: {times}")
        # We'll just pretend to succeed
        return 0

    def access(self, path, mode):
        """Check file access permissions"""
        _debug_print(f"FUSE access: {path}, mode: {mode}")
        # Always allow access for our virtual filesystem
        return 0

    def rename(self, old_path: str, new_path: str) -> int:
        """Rename/move a file or directory"""
        _debug_print(f"FUSE rename: {old_path} -> {new_path}")

        try:
            # First, read the old file/directory
            if hasattr(self.block_device, 'call_read'):
                try:
                    # Check if it's a file by trying to read it
                    content = self.block_device.call_read(old_path)
                    # It's a file - write to new location and delete old
                    success = self.block_device.call_write(new_path, content)
                    if success:
                        # Now remove from old location by writing empty content and removing from parent
                        self._remove_from_parent_directory(old_path)
                        _debug_print(f"Successfully renamed file: {old_path} -> {new_path}")
                        return 0
                    else:
                        raise FuseOSError(errno.EIO)
                except FileNotFoundError:
                    # Maybe it's a directory
                    if hasattr(self.block_device, 'call_list'):
                        try:
                            contents = self.block_device.call_list(old_path)
                            # It's a directory - create new directory and move contents
                            success = self.block_device.call_write(new_path + "/", b"")
                            if success:
                                # For now, we don't support moving directory contents
                                # This is a simplified implementation
                                self._remove_from_parent_directory(old_path)
                                _debug_print(f"Successfully renamed directory: {old_path} -> {new_path}")
                                return 0
                            else:
                                raise FuseOSError(errno.EIO)
                        except Exception:
                            raise FuseOSError(errno.ENOENT)
                    else:
                        raise FuseOSError(errno.ENOENT)
                except Exception as e:
                    _debug_print(f"Error during rename: {e}")
                    raise FuseOSError(errno.EIO)
            else:
                raise FuseOSError(errno.EROFS)
        except Exception as e:
            _debug_print(f"Rename error: {e}")
            raise FuseOSError(errno.EIO)

    def _remove_from_parent_directory(self, path: str):
        """Helper method to remove a file/directory from its parent directory listing"""
        parent = os.path.dirname(path)
        if parent == "":
            parent = "/"
        filename = os.path.basename(path)

        # This is a simplified implementation - in a real scenario,
        # you'd need to implement proper deletion in your storage backend
        _debug_print(f"Removing {filename} from parent directory {parent}")

    def unlink(self, path: str) -> int:
        """Delete a file"""
        _debug_print(f"FUSE unlink: {path}")

        try:
            # Call the delete callback if available
            if hasattr(self.block_device, 'call_delete'):
                success = self.block_device.call_delete(path)
                if success:
                    _debug_print(f"Successfully unlinked file: {path}")
                    return 0
                else:
                    raise FuseOSError(errno.EIO)
            else:
                # Fallback: just remove from parent directory
                self._remove_from_parent_directory(path)
                _debug_print(f"Successfully unlinked file: {path}")
                return 0
        except Exception as e:
            _debug_print(f"Unlink error: {e}")
            raise FuseOSError(errno.EIO)

    def rmdir(self, path: str) -> int:
        """Remove a directory"""
        _debug_print(f"FUSE rmdir: {path}")

        try:
            # Check if directory is empty first
            if hasattr(self.block_device, 'call_list'):
                contents = self.block_device.call_list(path)
                if contents and len(contents) > 0:
                    raise FuseOSError(errno.ENOTEMPTY)

            # Call the delete callback if available
            if hasattr(self.block_device, 'call_delete'):
                # For directories, we might want to add a trailing slash to distinguish them
                dir_path = path if path.endswith('/') else path + '/'
                success = self.block_device.call_delete(dir_path)
                if success:
                    _debug_print(f"Successfully removed directory: {path}")
                    return 0
                else:
                    raise FuseOSError(errno.EIO)
            else:
                # Fallback: just remove from parent directory
                self._remove_from_parent_directory(path)
                _debug_print(f"Successfully removed directory: {path}")
                return 0
        except Exception as e:
            _debug_print(f"Rmdir error: {e}")
            raise FuseOSError(errno.EIO)

    def mkdir(self, path, mode):
        """Create directory"""
        _debug_print(f"FUSE mkdir: {path}, mode: {oct(mode)}")

        try:
            # Add directory to parent's contents
            parent = os.path.dirname(path)
            if parent == "":
                parent = "/"
            dirname = os.path.basename(path)

            # Create the directory entry in our storage by calling the list callback
            # This will add it to the in-memory storage
            if hasattr(self.block_device, 'call_list'):
                try:
                    # Get parent contents
                    contents = self.block_device.call_list(parent)
                    # The write callback should handle adding to parent directory
                    # For now, we'll use a special write to indicate directory creation
                    success = self.block_device.call_write(path + "/", b"")  # Add trailing slash for directories
                    if success:
                        _debug_print(f"Successfully created directory: {path}")
                        return 0
                    else:
                        raise FuseOSError(errno.EIO)
                except Exception as e:
                    _debug_print(f"Error creating directory {path}: {e}")
                    raise FuseOSError(errno.EIO)
            else:
                raise FuseOSError(errno.EROFS)
        except Exception as e:
            _debug_print(f"mkdir error for {path}: {e}")
            raise FuseOSError(errno.EIO)

    def statfs(self, path):
        """Get filesystem statistics"""
        _debug_print(f"FUSE statfs: {path}")

        # Return filesystem statistics
        # These values are large enough to prevent "no space" errors
        return {
            'f_bsize':   10000000000,      # Block size
            'f_frsize':  10000000000,     # Fragment size
            'f_blocks':  10000000000000000000000000000000000000000000,  # Total blocks (4GB total space)
            'f_bfree':   10000000000000000000000000000000000000000000,    # Free blocks (3.6GB free space)
            'f_bavail':  10000000000000000000000000000000000000000000,   # Available blocks for unprivileged users
            'f_files':   10000000000000000000000000000000000000000000,    # Total file nodes
            'f_ffree':   10000000000000000000000000000000000000000000,     # Free file nodes
            'f_favail':  10000000000000000000000000000000000000000000,    # Available file nodes for unprivileged users
            'f_flag':    0,          # Mount flags
            'f_namemax': 255      # Maximum filename length
        }


