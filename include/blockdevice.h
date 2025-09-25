#pragma once

#include <string>
#include <functional>
#include <vector>
#include <pybind11/pybind11.h>
#include <pybind11/functional.h>
#include <pybind11/stl.h>

namespace py = pybind11;

class BlockDevice {
public:
    // Constructor with additional parameters
    explicit BlockDevice(const std::string& mountpoint, 
                        bool dolphin = false, 
                        const std::string& name = "");
    
    // Destructor
    ~BlockDevice() = default;
    
    // Getters
    const std::string& get_mountpoint() const { return mountpoint_; }
    const std::string& get_name() const { return name_; }
    bool get_dolphin_integration() const { return dolphin_integration_; }
    
    // Decorator methods that return the function (for chaining)
    py::object read_decorator(py::object func);
    py::object write_decorator(py::object func);
    py::object list_decorator(py::object func);
    py::object delete_decorator(py::object func);
    
    // Methods to set callbacks directly
    void set_read_callback(py::object func);
    void set_write_callback(py::object func);
    void set_list_callback(py::object func);
    void set_delete_callback(py::object func);
    
    // Methods to call the registered callbacks
    py::object call_read(const std::string& path);
    bool call_write(const std::string& path, const py::object& data);
    std::vector<std::string> call_list(const std::string& path);
    bool call_delete(const std::string& path);
    
    // FUSE filesystem methods
    void mount();
    void unmount();
    void start(bool foreground = false);
    void stop();
    bool is_mounted() const;

private:
    std::string mountpoint_;
    bool dolphin_integration_;
    std::string name_;
    bool mounted_;
    py::object read_callback_;
    py::object write_callback_;
    py::object list_callback_;
    py::object delete_callback_;
    py::object fuse_instance_;
};