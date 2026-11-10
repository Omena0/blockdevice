#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/functional.h>
#include "blockdevice.h"

namespace py = pybind11;

PYBIND11_MODULE(_blockdevice, m) {
    m.doc() = "BlockDevice C++ extension module";

    py::class_<BlockDevice>(m, "BlockDevice")
        .def(py::init<const std::string&, bool, const std::string&>(),
             py::arg("mountpoint"), py::arg("dolphin") = false, py::arg("name") = "",
             "Initialize BlockDevice with mountpoint, optional Dolphin integration, and custom name")

        .def_property_readonly("mountpoint", &BlockDevice::get_mountpoint,
                              "Get the mountpoint path")
        .def_property_readonly("name", &BlockDevice::get_name,
                              "Get the display name")
        .def_property_readonly("dolphin_integration", &BlockDevice::get_dolphin_integration,
                              "Get whether Dolphin integration is enabled")

        // Decorators - these are the main interface
        .def("read", &BlockDevice::read_decorator,
             "Decorator for read callback function")
        .def("write", &BlockDevice::write_decorator,
             "Decorator for write callback function")
        .def("list", &BlockDevice::list_decorator,
             "Decorator for list callback function")
        .def("delete", &BlockDevice::delete_decorator,
             "Decorator for delete callback function")
        .def("stat", &BlockDevice::stat_decorator,
             "Decorator for stat callback function")
        .def("mkdir", &BlockDevice::mkdir_decorator,
             "Decorator for mkdir callback function")
        .def("create", &BlockDevice::create_decorator,
             "Decorator for create (mkfile) callback function")
        .def("mknod", &BlockDevice::mknod_decorator,
             "Decorator for mknod callback function")
        .def("symlink", &BlockDevice::symlink_decorator,
             "Decorator for symlink callback function")
        .def("link", &BlockDevice::link_decorator,
             "Decorator for link (hard link) callback function")
        .def("rename", &BlockDevice::rename_decorator,
             "Decorator for rename callback function")
        .def("truncate", &BlockDevice::truncate_decorator,
             "Decorator for truncate callback function")
        .def("chmod", &BlockDevice::chmod_decorator,
             "Decorator for chmod callback function")
        .def("chown", &BlockDevice::chown_decorator,
             "Decorator for chown callback function")
        .def("utimens", &BlockDevice::utimens_decorator,
             "Decorator for utimens callback function")

        // Direct callback setters (alternative to decorators) - REMOVED.
        // Use the decorators above (read, write, list, ...) which are the
        // high-level registration API.

        // Internal callback invocation (used by FUSE operations).
        .def("_call_read", &BlockDevice::_call_read, py::arg("path"),
             "Call the registered read callback")
        .def("_call_write", &BlockDevice::_call_write, py::arg("path"), py::arg("data"),
             "Call the registered write callback")
        .def("_call_list", &BlockDevice::_call_list, py::arg("path"),
             "Call the registered list callback")
        .def("_call_delete", &BlockDevice::_call_delete, py::arg("path"),
             "Call the registered delete callback")
        .def("_call_stat", &BlockDevice::_call_stat, py::arg("path"),
             "Call the registered stat callback")
        .def("_call_mkdir", &BlockDevice::_call_mkdir, py::arg("path"), py::arg("mode"),
             "Call the registered mkdir callback")
        .def("_call_create", &BlockDevice::_call_create, py::arg("path"), py::arg("mode"),
             "Call the registered create callback")
        .def("_call_mknod", &BlockDevice::_call_mknod, py::arg("path"), py::arg("mode"), py::arg("dev"),
             "Call the registered mknod callback")
        .def("_call_symlink", &BlockDevice::_call_symlink, py::arg("target"), py::arg("source"),
             "Call the registered symlink callback")
        .def("_call_link", &BlockDevice::_call_link, py::arg("target"), py::arg("source"),
             "Call the registered link callback")
        .def("_call_rename", &BlockDevice::_call_rename, py::arg("old_path"), py::arg("new_path"),
             "Call the registered rename callback")
        .def("_call_truncate", &BlockDevice::_call_truncate, py::arg("path"), py::arg("length"),
             "Call the registered truncate callback")
        .def("_call_chmod", &BlockDevice::_call_chmod, py::arg("path"), py::arg("mode"),
             "Call the registered chmod callback")
        .def("_call_chown", &BlockDevice::_call_chown, py::arg("path"), py::arg("uid"), py::arg("gid"),
             "Call the registered chown callback")
        .def("_call_utimens", &BlockDevice::_call_utimens, py::arg("path"), py::arg("times"),
             "Call the registered utimens callback")

        // FUSE filesystem methods
        .def("_mount", &BlockDevice::_mount,
             "Mount the filesystem at the mountpoint (internal; use start/stop)")
        .def("_unmount", &BlockDevice::_unmount,
             "Unmount the filesystem (internal; use start/stop)")
        .def("start", &BlockDevice::start, py::arg("foreground") = false,
             "Start the FUSE filesystem (mounts and runs)")
        .def("stop", &BlockDevice::stop,
             "Stop and unmount the filesystem")
        .def("is_mounted", &BlockDevice::is_mounted,
             "Check if the filesystem is currently mounted")

        // String representation
        .def("__repr__", [](const BlockDevice& bd) {
            return "<BlockDevice(mountpoint='" + bd.get_mountpoint() + "')>";
        });
}
