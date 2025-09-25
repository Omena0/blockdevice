import pytest
import stat
import errno
import os
import tempfile
from unittest.mock import Mock
import blockdevice.fuse_ops as fuse_ops
import blockdevice.utils as utils


class TestBlockDeviceFUSE:
    """Test BlockDeviceFUSE operations."""

    def test_fuse_creation(self):
        """Test creating a BlockDeviceFUSE instance."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        assert fuse.block_device == mock_bd
        assert fuse.fd == 0
        assert fuse.open_files == {}
        assert isinstance(fuse.file_lock, type(fuse.file_lock))

    def test_get_next_fd(self):
        """Test _get_next_fd method."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        fd1 = fuse._get_next_fd()
        fd2 = fuse._get_next_fd()
        assert fd1 == 1
        assert fd2 == 2
        assert fuse.fd == 2

    def test_getattr_root(self):
        """Test getattr for root directory."""
        mock_bd = Mock()
        mock_bd.list_callback = Mock(return_value=[])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Test root directory attributes
        attrs = fuse.getattr('/')
        assert isinstance(attrs, dict)
        assert attrs['st_mode'] == (stat.S_IFDIR | 0o777)
        assert attrs['st_nlink'] == 2

    def test_readdir_root(self):
        """Test readdir for root directory."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=['file1', 'file2'])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Test reading root directory
        entries = fuse.readdir('/', None)
        assert '.' in entries
        assert '..' in entries
        assert 'file1' in entries
        assert 'file2' in entries

    def test_getattr_file(self):
        """Test getattr for a file."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=['test.txt'])
        mock_bd.call_read = Mock(return_value=b'hello')
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Test file attributes
        attrs = fuse.getattr('/test.txt')
        assert isinstance(attrs, dict)
        assert attrs['st_mode'] == (stat.S_IFREG | 0o666)
        assert attrs['st_size'] == 5  # len(b'hello')

    def test_getattr_file_not_exists(self):
        """Test getattr for a non-existent file."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=[])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Test non-existent file
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.getattr('/nonexistent.txt')
        assert exc_info.value.errno == fuse_ops.errno.ENOENT

    def test_open_existing_file(self):
        """Test opening an existing file."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=['test.txt'])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Open existing file
        fh = fuse.open('/test.txt', os.O_RDONLY)
        assert fh == 1
        assert fuse.open_files[1]['path'] == '/test.txt'

    def test_open_create_file(self):
        """Test opening a non-existing file with O_CREAT."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=[])
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Open non-existing file with O_CREAT
        fh = fuse.open('/new.txt', os.O_WRONLY | os.O_CREAT)
        assert fh == 1
        assert fuse.open_files[1]['path'] == '/new.txt'
        mock_bd.call_write.assert_called_with('/new.txt', b'')

    def test_read_file(self):
        """Test reading a file."""
        mock_bd = Mock()
        mock_bd.call_read = Mock(return_value=b'hello world')
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Read file
        data = fuse.read('/test.txt', 5, 0, 1)
        assert data == b'hello'

    def test_read_file_offset(self):
        """Test reading from a file at offset."""
        mock_bd = Mock()
        mock_bd.call_read = Mock(return_value=b'hello world')
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Read from offset 6, length 5
        data = fuse.read('/test.txt', 5, 6, 1)
        assert data == b'world'

    def test_write_file(self):
        """Test writing to a file."""
        mock_bd = Mock()
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Write file
        written = fuse.write('/test.txt', b'hello', 0, 1)
        assert written == 5
        mock_bd.call_write.assert_called_with('/test.txt', b'hello')

    def test_truncate_file(self):
        """Test truncating a file."""
        mock_bd = Mock()
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Truncate to 0
        fuse.truncate('/test.txt', 0)
        mock_bd.call_write.assert_called_with('/test.txt', b'')

    def test_truncate_file_extend(self):
        """Test truncating a file to extend it."""
        mock_bd = Mock()
        mock_bd.call_read = Mock(return_value=b'abc')
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Truncate to 5
        fuse.truncate('/test.txt', 5)
        mock_bd.call_write.assert_called_with('/test.txt', b'abc\x00\x00')

    def test_release_file(self):
        """Test releasing a file."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Assume file is open
        fuse.open_files[1] = {'path': '/test.txt', 'flags': os.O_RDONLY}

        # Release
        result = fuse.release('/test.txt', 1)
        assert result == 0
        assert 1 not in fuse.open_files

    def test_getattr_directory(self):
        """Test getattr for a directory."""
        mock_bd = Mock()
        mock_bd.call_list = Mock(return_value=['testdir/'])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Test directory attributes
        attrs = fuse.getattr('/testdir')
        assert isinstance(attrs, dict)
        assert attrs['st_mode'] == (stat.S_IFDIR | 0o777)
        assert attrs['st_nlink'] == 2

    def test_write_file_offset(self):
        """Test writing to a file at offset."""
        mock_bd = Mock()
        mock_bd.call_read = Mock(return_value=b'existing')
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Write at offset 2
        written = fuse.write('/test.txt', b'new', 2, 1)
        assert written == 3
        mock_bd.call_write.assert_called_with('/test.txt', b'exnewing')


class TestIntegration:
    """Integration tests for combined functionality."""

    def test_fuse_file_operations(self):
        """Test full file operations through FUSE."""
        mock_bd = Mock()
        # Setup mocks for various operations
        mock_bd.call_list = Mock(return_value=[])
        mock_bd.call_read = Mock(return_value=b'')
        mock_bd.call_write = Mock(return_value=True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        # Create and open a file
        fh = fuse.open('/test.txt', os.O_WRONLY | os.O_CREAT)
        assert fh == 1

        # Write to the file
        written = fuse.write('/test.txt', b'hello world', 0, fh)
        assert written == 11

        # Read from the file
        mock_bd.call_read = Mock(return_value=b'hello world')
        data = fuse.read('/test.txt', 5, 0, fh)
        assert data == b'hello'

        # Truncate the file
        fuse.truncate('/test.txt', 5)
        mock_bd.call_write.assert_called_with('/test.txt', b'hello')

        # Release the file
        result = fuse.release('/test.txt', fh)
        assert result == 0
        assert fh not in fuse.open_files

    def test_disk_object_persistence(self):
        """Test DiskObject persistence across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.pkl')

            # Create and populate first instance
            obj1 = utils.DiskObject(path)
            obj1['users'] = [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]
            obj1['settings'] = {'theme': 'dark', 'notifications': True}

            # Create second instance and verify data
            obj2 = utils.DiskObject(path)
            assert obj2['users'][0]['name'] == 'Alice'
            assert obj2['settings']['theme'] == 'dark'

            # Modify through second instance
            obj2['users'] = obj2['users'] + [{'name': 'Charlie', 'age': 35}]
            obj2['settings'] = {'theme': 'light', 'notifications': True}

            # Verify changes in third instance
            obj3 = utils.DiskObject(path)
            assert len(obj3['users']) == 3
            assert obj3['users'][2]['name'] == 'Charlie'
            assert obj3['settings']['theme'] == 'light'


if __name__ == "__main__":
    pytest.main([__file__])