import pytest
import tempfile
import os
import blockdevice.utils as utils
from unittest.mock import Mock, MagicMock


class TestObject:
    """Test the abstract Object class."""

    def test_abstract_methods(self):
        """Test that Object cannot be instantiated directly."""
        with pytest.raises(TypeError):
            utils.Object()

    def test_dict_interface(self):
        """Test dict-like interface."""
        class TestObj(utils.Object):
            def load(self): pass
            def save(self): pass

        obj = TestObj()
        obj['key'] = 'value'
        assert obj['key'] == 'value'
        assert 'key' in obj
        assert len(obj) == 1
        assert list(obj.keys()) == ['key']
        assert list(obj.values()) == ['value']
        assert list(obj.items()) == [('key', 'value')]

    def test_pop_and_clear(self):
        """Test pop and clear methods."""
        class TestObj(utils.Object):
            def load(self): pass
            def save(self): pass

        obj = TestObj()
        obj['a'] = 1
        obj['b'] = 2
        assert obj.pop('a') == 1
        assert 'a' not in obj
        obj.clear()
        assert len(obj) == 0


class TestDiskObject:
    """Test DiskObject functionality."""

    def test_disk_object_creation(self):
        """Test creating a DiskObject."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.pkl')
            obj = utils.DiskObject(path)
            assert obj.path == path
            assert len(obj) == 0

    def test_disk_object_save_load(self):
        """Test saving and loading data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.pkl')
            obj = utils.DiskObject(path)
            obj['test'] = 'value'
            obj['number'] = 42

            # Create new object to test loading
            obj2 = utils.DiskObject(path)
            assert obj2['test'] == 'value'
            assert obj2['number'] == 42

    def test_disk_object_nonexistent_file(self):
        """Test loading from nonexistent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'nonexistent.pkl')
            obj = utils.DiskObject(path)
            assert len(obj) == 0


class TestCompressedDiskObject:
    """Test CompressedDiskObject functionality."""

    def test_compressed_save_load(self):
        """Test compressed saving and loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.zst')
            obj = utils.CompressedDiskObject(path)
            obj['data'] = 'x' * 1000  # Larger data to test compression
            obj['number'] = 12345

            # Create new object to test loading
            obj2 = utils.CompressedDiskObject(path)
            assert obj2['data'] == 'x' * 1000
            assert obj2['number'] == 12345

    def test_compression_level(self):
        """Test custom compression level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'test.zst')
            obj = utils.CompressedDiskObject(path, compression_level=10)
            assert obj.compression_level == 10


class TestNetworkObject:
    """Test NetworkObject functionality."""

    def test_network_object_creation(self):
        """Test creating a NetworkObject."""
        from unittest.mock import patch
        with patch('blockdevice.utils.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.socket.return_value = mock_sock
            mock_sock.connect.side_effect = ConnectionError  # Force server mode
            obj = utils.NetworkObject('localhost', 1234)
            assert obj.host == 'localhost'
            assert obj.port == 1234

    def test_network_object_setitem(self):
        """Test setting item in NetworkObject."""
        from unittest.mock import patch
        with patch('blockdevice.utils.socket') as mock_socket:
            mock_sock = MagicMock()
            mock_socket.socket.return_value = mock_sock
            mock_sock.connect.side_effect = ConnectionError
            obj = utils.NetworkObject('localhost', 1234)
            obj['key'] = 'value'
            assert obj['key'] == 'value'


if __name__ == "__main__":
    pytest.main([__file__])