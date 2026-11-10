import os
from unittest.mock import Mock

import pytest

import blockdevice
from blockdevice import fuse_ops


class TestBlockDevice:
    """Test cases for the BlockDevice class."""

    def test_import(self):
        """Test that the module can be imported."""
        assert blockdevice is not None
        assert hasattr(blockdevice, 'BlockDevice')

    def test_blockdevice_creation(self):
        """Test creating a BlockDevice instance."""
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

    def test_stat_decorator(self):
        """Test the stat decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.stat
        def stat_file(path: str):
            return {"size": 42, "mode": 0o644}

        result = bd._call_stat("/foo.txt")
        assert result == {"size": 42, "mode": 0o644}

    def test_stat_decorator_registers_callback(self):
        """Test the stat decorator registers and invokes a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.stat
        def stat_file(path: str):
            return {"size": 100}

        result = bd._call_stat("/foo.txt")
        assert result == {"size": 100}

    def test_call_stat_no_callback(self):
        """Test call_stat raises when no stat callback is registered."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        with pytest.raises(RuntimeError, match="No stat callback registered"):
            bd._call_stat("/foo.txt")

    def test_filemode_exported(self):
        """Test that FileMode is exported from blockdevice."""
        assert hasattr(blockdevice, 'FileMode')

    def test_filemode_basic(self):
        """Test FileMode produces the expected permission bits."""
        fm = blockdevice.FileMode(type='file', owner='rwx', group='r--', other='r--')
        assert int(fm) == 0o100744

    def test_filemode_dir(self):
        """Test FileMode for a directory."""
        fm = blockdevice.FileMode(type='dir', owner='rwx', group='rwx', other='r-x')
        assert int(fm) == 0o40775

    def test_filemode_special_bits(self):
        """Test FileMode with setuid/sticky bits."""
        fm = blockdevice.FileMode(type='file', owner='rwx', setuid=True, sticky=True)
        assert int(fm) == 0o105744

    def test_filemode_invalid_type(self):
        """Test FileMode rejects invalid file types."""
        with pytest.raises(ValueError, match="Invalid file type"):
            blockdevice.FileMode(type='bogus')

    def test_filemode_invalid_perm(self):
        """Test FileMode rejects invalid permission strings."""
        with pytest.raises(ValueError, match="Invalid owner permissions"):
            blockdevice.FileMode(owner='abc')

    def test_stat_result_high_level(self):
        """Test StatResult with high-level argument names."""
        sr = blockdevice.StatResult(
            size=1024,
            mode=blockdevice.FileMode(type='file', owner='rwx', group='r--', other='r--'),
            modified=1234.0,
        )
        assert sr.size == 1024
        assert sr["size"] == 1024
        assert int(sr.mode) == 0o100744
        assert sr.modified == 1234.0

    def test_stat_result_dict_form(self):
        """Test StatResult with a dict mapping."""
        sr = blockdevice.StatResult({
            'size': 1024,
            'mode': blockdevice.FileMode(type='file', owner='rwx'),
        })
        assert sr.size == 1024

    def test_stat_result_rejects_invalid_key(self):
        """Test StatResult raises KeyError for invalid keys."""
        with pytest.raises(KeyError, match="Invalid stat key"):
            blockdevice.StatResult(bogus=1)

    def test_stat_result_rejects_invalid_item_assignment(self):
        """Test StatResult rejects setting invalid keys via __setitem__."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(KeyError, match="Invalid stat key"):
            sr['not_a_stat_key'] = 2

    def test_stat_result_rejects_invalid_attribute(self):
        """Test StatResult rejects setting invalid attributes."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(AttributeError, match="Invalid stat attribute"):
            sr.not_a_stat_key = 2

    def test_stat_result_attribute_unset_raises(self):
        """Test StatResult raises AttributeError for unset attributes."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(AttributeError):
            _ = sr.device

    def test_call_stat_returns_stat_result(self):
        """Test call_stat returns a StatResult when callback returns one."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.stat
        def stat_file(path: str) -> blockdevice.StatResult:
            return blockdevice.StatResult(
                size=77,
                mode=blockdevice.FileMode(type='file', owner='rwx', group='r--', other='r--'),
            )

        result = bd._call_stat("/foo.txt")
        assert isinstance(result, blockdevice.StatResult)
        assert result.size == 77

    def test_mkdir_decorator(self):
        """Test the mkdir decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.mkdir
        def mkdir_cb(path: str, mode: int) -> bool:
            return True

        assert bd._call_mkdir("/newdir", 0o755) is True

    def test_create_decorator(self):
        """Test the create decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.create
        def create_cb(path: str, mode: int) -> bool:
            return True

        assert bd._call_create("/newfile", 0o644) is True

    def test_mknod_decorator(self):
        """Test the mknod decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.mknod
        def mknod_cb(path: str, mode: int, dev: int) -> bool:
            return True

        assert bd._call_mknod("/device", 0o644, 0) is True

    def test_symlink_decorator(self):
        """Test the symlink decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.symlink
        def symlink_cb(target: str, source: str) -> bool:
            return True

        assert bd._call_symlink("/target", "/link") is True

    def test_link_decorator(self):
        """Test the link decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.link
        def link_cb(target: str, source: str) -> bool:
            return True

        assert bd._call_link("/target", "/hardlink") is True

    def test_rename_decorator(self):
        """Test the rename decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.rename
        def rename_cb(old_path: str, new_path: str) -> bool:
            return True

        assert bd._call_rename("/old", "/new") is True

    def test_truncate_decorator(self):
        """Test the truncate decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.truncate
        def truncate_cb(path: str, length: int) -> bool:
            return True

        assert bd._call_truncate("/file", 100) is True

    def test_chmod_decorator(self):
        """Test the chmod decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.chmod
        def chmod_cb(path: str, mode: int) -> bool:
            return True

        assert bd._call_chmod("/file", 0o755) is True

    def test_chown_decorator(self):
        """Test the chown decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.chown
        def chown_cb(path: str, uid: int, gid: int) -> bool:
            return True

        assert bd._call_chown("/file", 1000, 1000) is True

    def test_utimens_decorator(self):
        """Test the utimens decorator registers a callback."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.utimens
        def utimens_cb(path: str, times: tuple) -> bool:
            return True

        assert bd._call_utimens("/file", (1.0, 2.0)) is True

    def test_new_callback_no_registration(self):
        """Test that calling without a registered callback returns False."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        assert bd._call_mkdir("/dir", 0o755) is False
        assert bd._call_create("/file", 0o644) is False
        assert bd._call_mknod("/node", 0o644, 0) is False
        assert bd._call_symlink("/target", "/link") is False
        assert bd._call_link("/target", "/hard") is False
        assert bd._call_rename("/old", "/new") is False
        assert bd._call_truncate("/file", 100) is False
        assert bd._call_chmod("/file", 0o755) is False
        assert bd._call_chown("/file", 1000, 1000) is False
        assert bd._call_utimens("/file", (1.0, 2.0)) is False

    def test_callback_returns_false(self):
        """Test that callbacks returning False return False from call methods."""
        bd = blockdevice.BlockDevice("/tmp/test_mount", dolphin=False, name="test")

        @bd.mkdir
        def mkdir_cb(path: str, mode: int) -> bool:
            return False

        assert bd._call_mkdir("/dir", 0o755) is False


class TestFileMode:
    """Test cases for the FileMode class."""

    def test_filemode_default(self):
        """Test FileMode with all defaults."""
        fm = blockdevice.FileMode()
        assert int(fm) == 0o100744  # regular file, rwxr--r--

    def test_filemode_all_types(self):
        """Test FileMode for all file types."""
        assert int(blockdevice.FileMode(type="file")) & 0o170000 == 0o100000
        assert int(blockdevice.FileMode(type="dir")) & 0o170000 == 0o040000
        assert int(blockdevice.FileMode(type="link")) & 0o170000 == 0o120000
        assert int(blockdevice.FileMode(type="socket")) & 0o170000 == 0o140000
        assert int(blockdevice.FileMode(type="block")) & 0o170000 == 0o060000
        assert int(blockdevice.FileMode(type="char")) & 0o170000 == 0o020000
        assert int(blockdevice.FileMode(type="fifo")) & 0o170000 == 0o010000

    def test_filemode_permissions(self):
        """Test FileMode permission bits."""
        fm = blockdevice.FileMode(type="file", owner="rwx", group="rwx", other="rwx")
        assert int(fm) == 0o100777

        fm = blockdevice.FileMode(type="file", owner="---", group="---", other="---")
        assert int(fm) == 0o100000

        fm = blockdevice.FileMode(type="file", owner="r-x", group="r--", other="---")
        assert int(fm) == 0o100540

    def test_filemode_special_bits(self):
        """Test FileMode special bits."""
        fm = blockdevice.FileMode(type="file", setuid=True)
        assert int(fm) & 0o4000 == 0o4000

        fm = blockdevice.FileMode(type="file", setgid=True)
        assert int(fm) & 0o2000 == 0o2000

        fm = blockdevice.FileMode(type="file", sticky=True)
        assert int(fm) & 0o1000 == 0o1000

    def test_filemode_all_together(self):
        """Test FileMode with all options combined."""
        fm = blockdevice.FileMode(
            type="dir",
            owner="rwx",
            group="rwx",
            other="rwx",
            setuid=True,
            setgid=True,
            sticky=True,
        )
        assert int(fm) == 0o047777

    def test_filemode_invalid_type(self):
        """Test FileMode rejects invalid file types."""
        with pytest.raises(ValueError, match="Invalid file type"):
            blockdevice.FileMode(type="bogus")

    def test_filemode_invalid_perm_owner(self):
        """Test FileMode rejects invalid owner permissions."""
        with pytest.raises(ValueError, match="Invalid owner permissions"):
            blockdevice.FileMode(owner="abc")

    def test_filemode_invalid_perm_group(self):
        """Test FileMode rejects invalid group permissions."""
        with pytest.raises(ValueError, match="Invalid group permissions"):
            blockdevice.FileMode(group="qqq")

    def test_filemode_invalid_perm_other(self):
        """Test FileMode rejects invalid other permissions."""
        with pytest.raises(ValueError, match="Invalid other permissions"):
            blockdevice.FileMode(other="qqq")

    def test_filemode_behaves_like_int(self):
        """Test FileMode can be used as int in bitwise operations."""
        fm = blockdevice.FileMode(type="file", owner="rwx", group="r--", other="r--")
        assert fm | 0o400 == 0o100744 | 0o400
        assert fm & 0o777 == 0o744
        assert int(fm) == 0o100744

    def test_filemode_repr(self):
        """Test FileMode repr."""
        fm = blockdevice.FileMode(type="file", owner="rwx", group="r--")
        repr_str = repr(fm)
        assert "FileMode" in repr_str
        assert "type='file'" in repr_str
        assert "owner='rwx'" in repr_str


class TestStatResult:
    """Test cases for the StatResult class."""

    def test_stat_result_empty(self):
        """Test creating an empty StatResult."""
        sr = blockdevice.StatResult()
        assert len(sr) == 0

    def test_stat_result_all_keys(self):
        """Test StatResult with all valid keys."""
        sr = blockdevice.StatResult(
            size=1024,
            mode=0o644,
            modified=1234.0,
            accessed=5678.0,
            created=9012.0,
            owner=1000,
            group=1000,
            nlink=1,
            inode=42,
            device=0,
        )
        assert sr.size == 1024
        assert sr.mode == 0o644
        assert sr.modified == 1234.0
        assert sr.accessed == 5678.0
        assert sr.created == 9012.0
        assert sr.owner == 1000
        assert sr.group == 1000
        assert sr.nlink == 1
        assert sr.inode == 42
        assert sr.device == 0

    def test_stat_result_dict_access(self):
        """Test StatResult dictionary access."""
        sr = blockdevice.StatResult(size=1024, mode=0o644)
        assert sr["size"] == 1024
        assert sr["mode"] == 0o644

    def test_stat_result_attribute_access(self):
        """Test StatResult attribute access."""
        sr = blockdevice.StatResult(size=1024, mode=0o644)
        assert sr.size == 1024
        assert sr.mode == 0o644

    def test_stat_result_dict_and_attribute_sync(self):
        """Test that dict and attribute access stay in sync."""
        sr = blockdevice.StatResult(size=100)
        sr["size"] = 200
        assert sr.size == 200

        sr.size = 300
        assert sr["size"] == 300

    def test_stat_result_rejects_invalid_key(self):
        """Test StatResult raises KeyError for invalid keys."""
        with pytest.raises(KeyError, match="Invalid stat key"):
            blockdevice.StatResult(bogus=1)

    def test_stat_result_rejects_invalid_item_assignment(self):
        """Test StatResult rejects setting invalid keys via __setitem__."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(KeyError, match="Invalid stat key"):
            sr["not_a_stat_key"] = 2

    def test_stat_result_rejects_invalid_attribute(self):
        """Test StatResult rejects setting invalid attributes."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(AttributeError, match="Invalid stat attribute"):
            sr.not_a_stat_key = 2

    def test_stat_result_attribute_unset_raises(self):
        """Test StatResult raises AttributeError for unset attributes."""
        sr = blockdevice.StatResult(size=1)
        with pytest.raises(AttributeError):
            _ = sr.device

    def test_stat_result_filemode_value(self):
        """Test StatResult with FileMode as mode value."""
        fm = blockdevice.FileMode(type="file", owner="rwx")
        sr = blockdevice.StatResult(mode=fm, size=500)
        assert int(sr.mode) == int(fm)
        assert sr.size == 500

    def test_stat_result_dict_form(self):
        """Test StatResult with a dict mapping."""
        sr = blockdevice.StatResult({"size": 1024, "mode": 0o644})
        assert sr.size == 1024
        assert sr.mode == 0o644

    def test_stat_result_update(self):
        """Test StatResult update method."""
        sr = blockdevice.StatResult(size=100)
        sr.update(size=200, mode=0o644)
        assert sr.size == 200
        assert sr.mode == 0o644

    def test_stat_result_update_rejects_invalid(self):
        """Test StatResult update rejects invalid keys."""
        sr = blockdevice.StatResult(size=100)
        with pytest.raises(KeyError, match="Invalid stat key"):
            sr.update(bogus=1)

    def test_stat_result_setdefault(self):
        """Test StatResult setdefault."""
        sr = blockdevice.StatResult(size=100)
        assert sr.setdefault("size", 300) == 100
        assert sr.setdefault("mode", 0o644) == 0o644
        assert sr.size == 100
        assert sr.mode == 0o644

    def test_stat_result_setdefault_rejects_invalid(self):
        """Test StatResult setdefault rejects invalid keys."""
        sr = blockdevice.StatResult(size=100)
        with pytest.raises(KeyError, match="Invalid stat key"):
            sr.setdefault("bogus", 1)


class TestFUSEOps:
    """Test cases for FUSE operations with proper bool-returning mocks."""

    def _make_mock_bd(self, **callbacks):
        """Create a mock BlockDevice with specified callbacks."""
        mock_bd = Mock()
        for name, cb in callbacks.items():
            mock_cb = Mock(side_effect=cb)
            setattr(mock_bd, f"_call_{name}", mock_cb)
        return mock_bd

    def test_chmod_with_callback(self):
        """Test chmod with registered callback."""
        mock_bd = self._make_mock_bd(chmod=lambda path, mode: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.chmod("/file", 0o755)
        assert result == 0
        mock_bd._call_chmod.assert_called_once_with("/file", 0o755)

    def test_chmod_without_callback(self):
        """Test chmod without registered callback (should succeed)."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.chmod("/file", 0o755)
        assert result == 0

    def test_chmod_callback_false(self):
        """Test chmod when callback returns False."""
        mock_bd = self._make_mock_bd(chmod=lambda path, mode: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.chmod("/file", 0o755)
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_chown_with_callback(self):
        """Test chown with registered callback."""
        mock_bd = self._make_mock_bd(chown=lambda path, uid, gid: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.chown("/file", 1000, 1000)
        assert result == 0
        mock_bd._call_chown.assert_called_once_with("/file", 1000, 1000)

    def test_chown_callback_false(self):
        """Test chown when callback returns False."""
        mock_bd = self._make_mock_bd(chown=lambda path, uid, gid: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.chown("/file", 1000, 1000)
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_utimens_with_callback(self):
        """Test utimens with registered callback."""
        mock_bd = self._make_mock_bd(utimens=lambda path, times: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.utimens("/file", (1.0, 2.0))
        assert result == 0
        mock_bd._call_utimens.assert_called_once_with("/file", (1.0, 2.0))

    def test_utimens_callback_false(self):
        """Test utimens when callback returns False."""
        mock_bd = self._make_mock_bd(utimens=lambda path, times: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.utimens("/file", (1.0, 2.0))
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_access_always_allows(self):
        """Test access always returns 0."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.access("/file", os.R_OK)
        assert result == 0

    def test_rename_with_callback(self):
        """Test rename with registered callback."""
        mock_bd = self._make_mock_bd(rename=lambda old, new: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.rename("/old", "/new")
        assert result == 0
        mock_bd._call_rename.assert_called_once_with("/old", "/new")

    def test_rename_callback_false(self):
        """Test rename when callback returns False."""
        mock_bd = self._make_mock_bd(rename=lambda old, new: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.rename("/old", "/new")
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_unlink_with_callback(self):
        """Test unlink with registered callback."""
        mock_bd = self._make_mock_bd(delete=lambda path: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.unlink("/file")
        assert result == 0
        mock_bd._call_delete.assert_called_once_with("/file")

    def test_unlink_callback_false(self):
        """Test unlink when callback returns False."""
        mock_bd = self._make_mock_bd(delete=lambda path: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.unlink("/file")
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_rmdir_empty_with_callback(self):
        """Test rmdir on empty directory with callback."""
        mock_bd = self._make_mock_bd(
            list=lambda path: [],
            delete=lambda path: True,
        )
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.rmdir("/dir")
        assert result == 0

    def test_rmdir_not_empty(self):
        """Test rmdir on non-empty directory raises ENOTEMPTY."""
        mock_bd = self._make_mock_bd(list=lambda path: ["file1"])
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.rmdir("/dir")
        assert exc_info.value.errno == fuse_ops.errno.ENOTEMPTY

    def test_mkdir_with_callback(self):
        """Test mkdir with registered callback."""
        mock_bd = self._make_mock_bd(mkdir=lambda path, mode: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.mkdir("/dir", 0o755)
        assert result == 0
        mock_bd._call_mkdir.assert_called_once_with("/dir", 0o755)

    def test_mkdir_callback_false(self):
        """Test mkdir when callback returns False."""
        mock_bd = self._make_mock_bd(mkdir=lambda path, mode: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.mkdir("/dir", 0o755)
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_create_with_callback(self):
        """Test create with registered callback."""
        mock_bd = self._make_mock_bd(create=lambda path, mode: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        fd = fuse.create("/file", 0o644)
        assert isinstance(fd, int)
        assert fd > 0
        mock_bd._call_create.assert_called_once_with("/file", 0o644)

    def test_create_callback_false(self):
        """Test create when callback returns False."""
        mock_bd = self._make_mock_bd(create=lambda path, mode: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.create("/file", 0o644)
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_mknod_with_callback(self):
        """Test mknod with registered callback."""
        mock_bd = self._make_mock_bd(mknod=lambda path, mode, dev: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.mknod("/dev", 0o644, 0)
        assert result == 0
        mock_bd._call_mknod.assert_called_once_with("/dev", 0o644, 0)

    def test_mknod_callback_false(self):
        """Test mknod when callback returns False."""
        mock_bd = self._make_mock_bd(mknod=lambda path, mode, dev: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.mknod("/dev", 0o644, 0)
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_symlink_with_callback(self):
        """Test symlink with registered callback."""
        mock_bd = self._make_mock_bd(symlink=lambda target, source: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.symlink("/target", "/link")
        assert result == 0
        mock_bd._call_symlink.assert_called_once_with("/target", "/link")

    def test_symlink_callback_false(self):
        """Test symlink when callback returns False."""
        mock_bd = self._make_mock_bd(symlink=lambda target, source: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.symlink("/target", "/link")
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_link_with_callback(self):
        """Test link with registered callback."""
        mock_bd = self._make_mock_bd(link=lambda target, source: True)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        result = fuse.link("/target", "/hard")
        assert result == 0
        mock_bd._call_link.assert_called_once_with("/target", "/hard")

    def test_link_callback_false(self):
        """Test link when callback returns False."""
        mock_bd = self._make_mock_bd(link=lambda target, source: False)
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)
        with pytest.raises(fuse_ops.FuseOSError) as exc_info:
            fuse.link("/target", "/hard")
        assert exc_info.value.errno == fuse_ops.errno.EIO

    def test_simple_ops_return_zero(self):
        """Test simple FUSE ops that always return 0."""
        mock_bd = Mock()
        fuse = fuse_ops.BlockDeviceFUSE(mock_bd)

        assert fuse.init(None) == 0
        assert fuse.destroy(None) is None
        assert fuse.fsyncdir("/path", False, 1) == 0
        assert fuse.opendir("/path", Mock()) == 0
        assert fuse.releasedir("/path", Mock()) == 0
        assert fuse.statfs("/path") == fuse.statfs("/path")  # deterministic
        assert fuse.lock("/path", 1, 1, Mock()) == 0
        assert fuse.flush("/path", 1) == 0
        assert fuse.fsync("/path", False, 1) == 0


if __name__ == "__main__":
    pytest.main([__file__])
