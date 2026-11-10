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
    py::object stat_decorator(py::object func);
    py::object mkdir_decorator(py::object func);
    py::object create_decorator(py::object func);
    py::object mknod_decorator(py::object func);
    py::object symlink_decorator(py::object func);
    py::object link_decorator(py::object func);
    py::object rename_decorator(py::object func);
    py::object truncate_decorator(py::object func);
    py::object chmod_decorator(py::object func);
    py::object chown_decorator(py::object func);
    py::object utimens_decorator(py::object func);

    // Internal callback invocation (used by FUSE operations, not part of the
    // high-level user API - callbacks are registered via the decorators above)
    py::object _call_read(const std::string& path);
    bool _call_write(const std::string& path, const py::object& data);
    std::vector<std::string> _call_list(const std::string& path);
    bool _call_delete(const std::string& path);
    py::object _call_stat(const std::string& path);
    bool _call_mkdir(const std::string& path, int mode);
    bool _call_create(const std::string& path, int mode);
    bool _call_mknod(const std::string& path, int mode, int dev);
    bool _call_symlink(const std::string& target, const std::string& source);
    bool _call_link(const std::string& target, const std::string& source);
    bool _call_rename(const std::string& old_path, const std::string& new_path);
    bool _call_truncate(const std::string& path, int length);
    bool _call_chmod(const std::string& path, int mode);
    bool _call_chown(const std::string& path, int uid, int gid);
    bool _call_utimens(const std::string& path, const py::object& times);

    // FUSE filesystem lifecycle. start()/stop() are the public high-level API;
    // _mount()/_unmount() are the low-level mounting primitives.
    void _mount();
    void _unmount();
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
    py::object stat_callback_;
    py::object mkdir_callback_;
    py::object create_callback_;
    py::object mknod_callback_;
    py::object symlink_callback_;
    py::object link_callback_;
    py::object rename_callback_;
    py::object truncate_callback_;
    py::object chmod_callback_;
    py::object chown_callback_;
    py::object utimens_callback_;
    py::object fuse_instance_;
};
