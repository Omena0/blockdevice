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
        
        // Direct callback setters (alternative to decorators)
        .def("set_read_callback", &BlockDevice::set_read_callback,
             "Set the read callback function directly")
        .def("set_write_callback", &BlockDevice::set_write_callback,
             "Set the write callback function directly")
        .def("set_list_callback", &BlockDevice::set_list_callback,
             "Set the list callback function directly")
        .def("set_delete_callback", &BlockDevice::set_delete_callback,
             "Set the delete callback function directly")
        
        // Methods to call the registered callbacks
        .def("call_read", &BlockDevice::call_read, py::arg("path"),
             "Call the registered read callback")
        .def("call_write", &BlockDevice::call_write, py::arg("path"), py::arg("data"),
             "Call the registered write callback")
        .def("call_list", &BlockDevice::call_list, py::arg("path"),
             "Call the registered list callback")
        .def("call_delete", &BlockDevice::call_delete, py::arg("path"),
             "Call the registered delete callback")
        
        // FUSE filesystem methods
        .def("mount", &BlockDevice::mount,
             "Mount the filesystem at the mountpoint")
        .def("unmount", &BlockDevice::unmount,
             "Unmount the filesystem")
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