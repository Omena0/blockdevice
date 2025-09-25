"""
Type stubs for BlockDevice C++ extension module
"""

from typing import Any, Callable, List, Optional, TypeVar, overload
from typing_extensions import ParamSpec

P = ParamSpec('P')
T = TypeVar('T')

# Type aliases for callback functions
ReadCallback = Callable[[str], bytes | str]
WriteCallback = Callable[[str, bytes], bool]
ListCallback = Callable[[str], List[str]]
DeleteCallback = Callable[[str], bool]

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
        ...
    
    @property
    def mountpoint(self) -> str:
        """Get the mountpoint path."""
        ...
    
    @property
    def name(self) -> str:
        """Get the display name."""
        ...
    
    @property
    def dolphin_integration(self) -> bool:
        """Get whether Dolphin integration is enabled."""
        ...
    
    # Decorator methods
    def read(self, func: Callable[[str], T]) -> Callable[[str], T]:
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
        ...
    
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
        ...
    
    def list(self, func: Callable[[str], List[str]]) -> Callable[[str], List[str]]:
        """
        Decorator to register a directory listing callback function.
        
        The decorated function should take a directory path (str) and return
        a list of filenames/subdirectories in that directory.
        
        Example:
            @bd.list
            def list_directory(path: str) -> List[str]:
                return ["file1.txt", "subdir/"]
        
        Args:
            func: Function that takes a path and returns list of contents
            
        Returns:
            The same function (for decorator chaining)
        """
        ...
    
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
        ...
    
    # Direct callback setters (alternative to decorators)
    def set_read_callback(self, func: ReadCallback) -> None:
        """Set the read callback function directly."""
        ...
    
    def set_write_callback(self, func: WriteCallback) -> None:
        """Set the write callback function directly."""
        ...
    
    def set_list_callback(self, func: ListCallback) -> None:
        """Set the list callback function directly."""
        ...
    
    def set_delete_callback(self, func: DeleteCallback) -> None:
        """Set the delete callback function directly."""
        ...
    
    # Callback invocation methods (used internally by FUSE operations)
    def call_read(self, path: str) -> Any:
        """Call the registered read callback with the given path."""
        ...
    
    def call_write(self, path: str, data: Any) -> bool:
        """Call the registered write callback with the given path and data."""
        ...
    
    def call_list(self, path: str) -> List[str]:
        """Call the registered list callback with the given path."""
        ...
    
    def call_delete(self, path: str) -> bool:
        """Call the registered delete callback with the given path."""
        ...
    
    # FUSE filesystem methods
    def mount(self) -> None:
        """Mount the filesystem at the specified mountpoint."""
        ...
    
    def unmount(self) -> None:
        """Unmount the filesystem."""
        ...
    
    def start(self, foreground: bool = True) -> None:
        """Start the FUSE filesystem."""
        ...
    
    def stop(self) -> None:
        """Stop the FUSE filesystem."""
        ...
    
    def is_mounted(self) -> bool:
        """Check if the filesystem is currently mounted."""
        ...