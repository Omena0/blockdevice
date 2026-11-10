#include "blockdevice.h"
#include <stdexcept>

BlockDevice::BlockDevice(const std::string& mountpoint, bool dolphin, const std::string& name) 
    : mountpoint_(mountpoint), 
      dolphin_integration_(dolphin),
      name_(name.empty() ? mountpoint : name),
      mounted_(false) {
    // Initialize callbacks to None
    read_callback_ = py::none();
    write_callback_ = py::none();
    list_callback_ = py::none();
    delete_callback_ = py::none();
    stat_callback_ = py::none();
    mkdir_callback_ = py::none();
    create_callback_ = py::none();
    mknod_callback_ = py::none();
    symlink_callback_ = py::none();
    link_callback_ = py::none();
    rename_callback_ = py::none();
    truncate_callback_ = py::none();
    chmod_callback_ = py::none();
    chown_callback_ = py::none();
    utimens_callback_ = py::none();
    fuse_instance_ = py::none();
}

py::object BlockDevice::read_decorator(py::object func) {
    read_callback_ = func;
    return func;  // Return the function for chaining
}

py::object BlockDevice::write_decorator(py::object func) {
    write_callback_ = func;
    return func;  // Return the function for chaining
}

py::object BlockDevice::list_decorator(py::object func) {
    list_callback_ = func;
    return func;  // Return the function for chaining
}

py::object BlockDevice::delete_decorator(py::object func) {
    delete_callback_ = func;
    return func;  // Return the function for chaining
}

py::object BlockDevice::stat_decorator(py::object func) {
    stat_callback_ = func;
    return func;  // Return the function for chaining
}

py::object BlockDevice::mkdir_decorator(py::object func) {
    mkdir_callback_ = func;
    return func;
}

py::object BlockDevice::create_decorator(py::object func) {
    create_callback_ = func;
    return func;
}

py::object BlockDevice::mknod_decorator(py::object func) {
    mknod_callback_ = func;
    return func;
}

py::object BlockDevice::symlink_decorator(py::object func) {
    symlink_callback_ = func;
    return func;
}

py::object BlockDevice::link_decorator(py::object func) {
    link_callback_ = func;
    return func;
}

py::object BlockDevice::rename_decorator(py::object func) {
    rename_callback_ = func;
    return func;
}

py::object BlockDevice::truncate_decorator(py::object func) {
    truncate_callback_ = func;
    return func;
}

py::object BlockDevice::chmod_decorator(py::object func) {
    chmod_callback_ = func;
    return func;
}

py::object BlockDevice::chown_decorator(py::object func) {
    chown_callback_ = func;
    return func;
}

py::object BlockDevice::utimens_decorator(py::object func) {
    utimens_callback_ = func;
    return func;
}

bool BlockDevice::_call_mkdir(const std::string& path, int mode) {
    if (mkdir_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = mkdir_callback_(path, mode);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling mkdir callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_create(const std::string& path, int mode) {
    if (create_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = create_callback_(path, mode);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling create callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_mknod(const std::string& path, int mode, int dev) {
    if (mknod_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = mknod_callback_(path, mode, dev);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling mknod callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_symlink(const std::string& target, const std::string& source) {
    if (symlink_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = symlink_callback_(target, source);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling symlink callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_link(const std::string& target, const std::string& source) {
    if (link_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = link_callback_(target, source);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling link callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_rename(const std::string& old_path, const std::string& new_path) {
    if (rename_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = rename_callback_(old_path, new_path);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling rename callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_truncate(const std::string& path, int length) {
    if (truncate_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = truncate_callback_(path, length);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling truncate callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_chmod(const std::string& path, int mode) {
    if (chmod_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = chmod_callback_(path, mode);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling chmod callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_chown(const std::string& path, int uid, int gid) {
    if (chown_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = chown_callback_(path, uid, gid);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling chown callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_utimens(const std::string& path, const py::object& times) {
    if (utimens_callback_.is_none()) {
        return false;
    }
    try {
        py::object result = utimens_callback_(path, times);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling utimens callback: " + std::string(e.what()));
    }
}

py::object BlockDevice::_call_stat(const std::string& path) {
    if (stat_callback_.is_none()) {
        throw std::runtime_error("No stat callback registered");
    }
    
    try {
        return stat_callback_(path);
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling stat callback: " + std::string(e.what()));
    }
}

py::object BlockDevice::_call_read(const std::string& path) {
    if (read_callback_.is_none()) {
        throw std::runtime_error("No read callback registered");
    }
    
    try {
        return read_callback_(path);
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling read callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_write(const std::string& path, const py::object& data) {
    if (write_callback_.is_none()) {
        throw std::runtime_error("No write callback registered");
    }
    
    try {
        py::object result = write_callback_(path, data);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling write callback: " + std::string(e.what()));
    }
}

std::vector<std::string> BlockDevice::_call_list(const std::string& path) {
    if (list_callback_.is_none()) {
        throw std::runtime_error("No list callback registered");
    }
    
    try {
        py::object result = list_callback_(path);
        return result.cast<std::vector<std::string>>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling list callback: " + std::string(e.what()));
    }
}

bool BlockDevice::_call_delete(const std::string& path) {
    if (delete_callback_.is_none()) {
        throw std::runtime_error("No delete callback registered");
    }
    
    try {
        py::object result = delete_callback_(path);
        return result.cast<bool>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling delete callback: " + std::string(e.what()));
    }
}

void BlockDevice::_mount() {
    if (mounted_) {
        throw std::runtime_error("Filesystem already mounted");
    }
    
    try {
        // Import the Python modules
        py::module_ os = py::module_::import("os");
        py::module_ blockdevice = py::module_::import("blockdevice.fuse_ops");
        
        // Create mountpoint directory if it doesn't exist
        if (!os.attr("path").attr("exists")(mountpoint_).cast<bool>()) {
            try {
                os.attr("makedirs")(mountpoint_);
            } catch (py::error_already_set e) {
                e.restore();
                if (PyErr_ExceptionMatches(PyExc_PermissionError)) {
                    PyErr_Clear();
                    throw std::runtime_error(
                        "Permission denied creating mountpoint '" + mountpoint_ + "'. "
                        "Run with sudo, or choose a writable mountpoint (e.g. /tmp/blockdevice)."
                    );
                }
                throw py::error_already_set();
            }
        }
        
        // Create FUSE operations instance
        py::object fuse_ops = blockdevice.attr("BlockDeviceFUSE")(*py::make_tuple(py::cast(this)));
        
        // Store for later use
        fuse_instance_ = fuse_ops;
        mounted_ = true;
        
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error mounting filesystem: " + std::string(e.what()));
    }
}

void BlockDevice::_unmount() {
    if (!mounted_) {
        throw std::runtime_error("Filesystem not mounted");
    }
    
    try {
        // Import subprocess to run fusermount
        py::module_ subprocess = py::module_::import("subprocess");
        
        // Unmount using fusermount
        py::list args;
        args.append("fusermount");
        args.append("-u");
        args.append(mountpoint_);
        
        subprocess.attr("run")(args, py::arg("check") = true);
        
        fuse_instance_ = py::none();
        mounted_ = false;
        
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error unmounting filesystem: " + std::string(e.what()));
    }
}

void BlockDevice::start(bool foreground) {
    if (!mounted_) {
        _mount();
    }
    
    try {
        // Import FUSE and other necessary modules
        py::module_ fuse_mod = py::module_::import("fuse");
        py::module_ os = py::module_::import("os");
        py::module_ atexit = py::module_::import("atexit");
        
        // Create cleanup function in Python
        py::object cleanup_func = py::cpp_function([this, os]() {
            try {
                if (this->is_mounted()) {
                    try {
                        this->_unmount();
                    } catch (const std::exception&) {
                        // If normal unmount fails, try force unmount
                        py::module_ subprocess = py::module_::import("subprocess");
                        py::list args;
                        args.append("fusermount");
                        args.append("-uz");  // -z for lazy unmount
                        args.append(this->mountpoint_);
                        try {
                            subprocess.attr("run")(args, py::arg("check") = false);
                        } catch (...) {
                            // Ignore force unmount failures
                        }
                    }
                }
                // Try to remove mount directory if it exists
                if (os.attr("path").attr("exists")(this->mountpoint_).cast<bool>()) {
                    try {
                        // First try to remove normally
                        os.attr("rmdir")(this->mountpoint_);
                    } catch (const py::error_already_set&) {
                        // If that fails, try to force remove
                        try {
                            py::module_ shutil = py::module_::import("shutil");
                            shutil.attr("rmtree")(this->mountpoint_, py::arg("ignore_errors") = true);
                        } catch (...) {
                            // Ignore all removal errors - best effort cleanup
                        }
                    }
                }
            } catch (...) {
                // Ignore all cleanup errors - this is best effort
            }
        });
        
        // Register cleanup function if running in foreground
        if (foreground) {
            atexit.attr("register")(cleanup_func);
        }
        
        // Create FUSE instance and start
        // Provide filesystem name (fsname), subtype and allow_other so desktop environments
        // can recognize this as a removable/media mount and the mount is accessible to other users
        // Prepare a short fsname (basename of name_ or mountpoint_) without slashes
        std::string fsname = name_.empty() ? mountpoint_ : name_;
        // Extract basename
        size_t pos = fsname.find_last_of('/');
        if (pos != std::string::npos && pos + 1 < fsname.size()) {
            fsname = fsname.substr(pos + 1);
        }
        if (fsname.empty()) {
            fsname = "blockdevice";
        }

        // Create FUSE instance passing fsname, subtype and allow_other as kwargs
        py::object fuse_instance = fuse_mod.attr("FUSE")(
            fuse_instance_,
            mountpoint_,
            py::arg("foreground") = foreground,
            py::arg("default_permissions") = true,
            py::arg("fsname") = fsname,
            py::arg("subtype") = std::string("blockdevice")
        );
        
        // If we reach here and foreground was true, FUSE has exited
        // Cleanup will be handled by atexit
        
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error starting FUSE filesystem: " + std::string(e.what()));
    }
}

void BlockDevice::stop() {
    if (mounted_) {
        _unmount();
    }
}

bool BlockDevice::is_mounted() const {
    return mounted_;
}