import pytest
import blockdevice


class TestBlockDevice:
    """Test cases for the BlockDevice class."""

    def test_import(self):
        """Test that the module can be imported."""
        assert blockdevice is not None
        assert hasattr(blockdevice, 'BlockDevice')

    def test_blockdevice_creation(self):
        """Test creating a BlockDevice instance."""
        # Create a BlockDevice instance (without mounting)
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")
        assert bd is not None
        assert bd.mountpoint == "/tmp/test_mount"
        assert bd.name == "test"
        assert not bd.is_mounted()

    def test_blockdevice_with_dolphin(self):
        """Test BlockDevice with dolphin integration enabled."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=True, name="test")
        assert bd.dolphin_integration == True

    def test_blockdevice_default_name(self):
        """Test BlockDevice with default name from mountpoint."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False)
        assert bd.name == "/tmp/test_mount"

    def test_blockdevice_custom_name(self):
        """Test BlockDevice with custom name."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="custom")
        assert bd.name == "custom"


if __name__ == "__main__":
    pytest.main([__file__])