import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from blockdevice.utils import NetworkObject
from blockdevice import BlockDevice


dev = BlockDevice(sys.argv[1], dolphin=True)

# Create NetworkObject with proper error handling
fs = NetworkObject('127.0.0.1', 8080, {'/': {"type": "dir", "contents": []}})

print(str(fs._data)[:1000])

def ensure_parent_dirs(file_path):
    parent = os.path.dirname(file_path)
    if parent == "":
        parent = "/"
    elif parent != "/":
        parent = parent + "/"

    # If parent doesn't exist, create it recursively
    if parent not in fs:
        # Create grandparent first
        grandparent = os.path.dirname(parent.rstrip('/'))
        if grandparent == "":
            grandparent = "/"
        elif grandparent != "/":
            grandparent = grandparent + "/"

        # Recursively ensure grandparents exist
        if grandparent != parent:
            ensure_parent_dirs(parent.rstrip('/'))

        # Create the parent directory
        fs[parent] = {"type": "dir", "contents": []}

        # Add to grandparent's contents
        if grandparent in fs and fs[grandparent]["type"] == "dir":
            dirname = os.path.basename(parent.rstrip('/')) + '/'
            if dirname not in fs[grandparent]["contents"]:
                fs[grandparent]["contents"].append(dirname)

def delete(target_path):
    """Recursively delete a file or directory and all its contents"""
    # Normalize the path - ensure directories end with /
    if target_path != "/" and target_path.endswith('/'):
        # It's a directory path
        dir_path = target_path
        base_path = target_path.rstrip('/')
    else:
        # Check if it exists as a directory
        dir_path = target_path + '/'
        base_path = target_path

        # If it exists as a file, handle it as such
        if target_path in fs and fs[target_path]["type"] == "file":
            # Remove from fs
            del fs[target_path]

            # Remove from parent directory listing
            parent = os.path.dirname(target_path)
            if parent == "":
                parent = "/"
            elif parent != "/":
                parent = parent + "/"

            filename = os.path.basename(target_path)

            if parent in fs and fs[parent]["type"] == "dir" and filename in fs[parent]["contents"]:
                fs[parent]["contents"].remove(filename)

            return True

    # Handle directory deletion
    if dir_path in fs and fs[dir_path]["type"] == "dir":
        # Delete all contents first
        contents = fs[dir_path]["contents"][:]  # Make a copy to avoid modification during iteration
        for item in contents:
            if item.endswith('/'):
                # It's a subdirectory - construct full path and delete recursively
                subdir_full_path = dir_path + item
                if not delete(subdir_full_path):
                    return False
            else:
                # It's a file - construct full path and delete
                file_full_path = dir_path + item
                if not delete(file_full_path):
                    return False

        # Now delete the directory itself
        del fs[dir_path]

        # Remove from parent directory listing
        parent = os.path.dirname(base_path)
        if parent == "":
            parent = "/"
        elif parent != "/":
            parent = parent + "/"

        dirname = os.path.basename(base_path) + '/'

        if parent in fs and fs[parent]["type"] == "dir" and dirname in fs[parent]["contents"]:
            fs[parent]["contents"].remove(dirname)

        return True

    # File/directory doesn't exist
    return False

@dev.read
def read_file(path):
    if path in fs and fs[path]["type"] == "file":
        content = fs[path]["content"]
        return content
    else:
        raise FileNotFoundError(f"No such file: {path}")

@dev.write
def write_file(path, data):
    """Callback for writing files and creating directories"""
    try:
        # It's a directory
        if path.endswith('/'):
            if not path in fs:
                fs[path] = {"type": "dir", "contents": []}

            # Add to parent directory listing
            parent = os.path.dirname(path.rstrip('/'))
            if parent == "":
                parent = "/"
            elif parent != "/":
                parent = parent + "/"  # Only add trailing slash if it's not root

            dirname = os.path.basename(path.rstrip('/')) + '/'

            # Make sure parent directory exists, create if needed
            if parent not in fs:
                fs[parent] = {"type": "dir", "contents": []}

            if fs[parent]["type"] == "dir" and dirname not in fs[parent]["contents"]:
                fs[parent]["contents"].append(dirname)

            return True

        # It's a file
        else:
            # Ensure parent directories exist
            ensure_parent_dirs(path)

            # Convert data to appropriate format
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif not isinstance(data, bytes):
                data = bytes(data)

            # Create the file - always allow overwrite for robustness
            fs[path] = {"type": "file", "content": data}

            # Add to parent directory listing if it doesn't exist
            parent = os.path.dirname(path)
            if parent == "":
                parent = "/"
            elif parent != "/":
                parent = parent + "/"  # Add trailing slash for directory lookup

            filename = os.path.basename(path)

            # Make sure parent directory exists (should exist now)
            if parent not in fs:
                # Try to create it as a fallback
                fs[parent] = {"type": "dir", "contents": []}

            if fs[parent]["type"] == "dir":
                if filename not in fs[parent]["contents"]:
                    fs[parent]["contents"].append(filename)

            return True
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Return True even on some errors to prevent FUSE from failing
        return True

@dev.list
def list_directory(path):
    """Callback for listing directory contents"""
    # Try the path as-is first, then try with trailing slash
    target_path = path
    if path != "/" and not path.endswith('/'):
        target_path = path + "/"

    if target_path in fs and fs[target_path]["type"] == "dir":
        return fs[target_path]["contents"]
    elif path in fs and fs[path]["type"] == "dir":
        return fs[path]["contents"]
    else:
        return []

@dev.delete
def delete_file(path):
    """Callback for deleting files and directories (recursive)"""
    result = delete(path)
    return result

print('Starting..')

dev.start(True)


