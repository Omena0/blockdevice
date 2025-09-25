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
    fuse_instance_ = py::none();
}

py::object BlockDevice::read_decorator(py::object func) {
    set_read_callback(func);
    return func;  // Return the function for chaining
}

py::object BlockDevice::write_decorator(py::object func) {
    set_write_callback(func);
    return func;  // Return the function for chaining
}

py::object BlockDevice::list_decorator(py::object func) {
    set_list_callback(func);
    return func;  // Return the function for chaining
}

py::object BlockDevice::delete_decorator(py::object func) {
    set_delete_callback(func);
    return func;  // Return the function for chaining
}

void BlockDevice::set_read_callback(py::object func) {
    read_callback_ = func;
}

void BlockDevice::set_write_callback(py::object func) {
    write_callback_ = func;
}

void BlockDevice::set_list_callback(py::object func) {
    list_callback_ = func;
}

void BlockDevice::set_delete_callback(py::object func) {
    delete_callback_ = func;
}

py::object BlockDevice::call_read(const std::string& path) {
    if (read_callback_.is_none()) {
        throw std::runtime_error("No read callback registered");
    }
    
    try {
        return read_callback_(path);
    } catch (const py::error_already_set& e) {
        throw std::runtime_error("Error calling read callback: " + std::string(e.what()));
    }
}

bool BlockDevice::call_write(const std::string& path, const py::object& data) {
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

std::vector<std::string> BlockDevice::call_list(const std::string& path) {
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

bool BlockDevice::call_delete(const std::string& path) {
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

void BlockDevice::mount() {
    if (mounted_) {
        throw std::runtime_error("Filesystem already mounted");
    }
    
    try {
        // Import the Python modules
        py::module_ os = py::module_::import("os");
        py::module_ blockdevice = py::module_::import("blockdevice.fuse_ops");
        
        // Create mountpoint directory if it doesn't exist
        if (!os.attr("path").attr("exists")(mountpoint_).cast<bool>()) {
            os.attr("makedirs")(mountpoint_);
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

void BlockDevice::unmount() {
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
        mount();
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
                        this->unmount();
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
        unmount();
    }
}

bool BlockDevice::is_mounted() const {
    return mounted_;
}