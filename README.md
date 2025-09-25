# Blockdevice

[![Build](https://github.com/Omena0/blockdevice/actions/workflows/publish.yml/badge.svg)](https://github.com/Omena0/blockdevice/actions/workflows/publish.yml)
[![pytest](https://github.com/Omena0/blockdevice/actions/workflows/pytest.yml/badge.svg)](https://github.com/Omena0/blockdevice/actions/workflows/pytest.yml)
[![Coverage](https://img.shields.io/badge/coverage-48%25-brightgreen)](https://github.com/Omena0/blockdevice/actions/workflows/pytest.yml)

A Python library for creating and managing block devices with FUSE filesystem support. Provides persistent object storage with compression options and real-time synchronization capabilities.

## Features

- **Block Device Operations**: C++ extension for efficient block device operations
- **FUSE Filesystem**: Mount block devices as user-space filesystems
- **Persistent Storage**: Multiple storage backends including disk-based and compressed storage
- **Real-time Sync**: Network synchronization for distributed applications
- **Python Integration**: Seamless integration with Python applications

## Installation

### From Source
```bash
git clone https://github.com/Omena0/blockdevice.git
cd blockdevice
pip install .
```

## Quick Start

### Basic Usage

```python
from blockdevice import BlockDevice, DiskObject

# Create a block device
dev = BlockDevice("/path/to/device", dolphin=True)

# Create persistent storage
storage = DiskObject("data.pkl")
storage['key'] = 'value'
print(storage['key'])  # 'value'

dev.start(True) # Start FUSE filesystem
```

### Compressed Storage

```python
from blockdevice import CompressedDiskObject

# Create compressed persistent storage
storage = CompressedDiskObject("data.zst", compression_level=10)
storage['large_data'] = 'x' * 10000  # Automatically compressed
```

### Network Synchronization

```python
from blockdevice import NetworkObject

# Create synchronized object (connects to server or becomes server)
sync_obj = NetworkObject('localhost', 8080)
sync_obj['shared_data'] = 'available on all connected instances'
```

## Architecture

The library consists of several key components:

- **BlockDevice**: C++ extension providing low-level block operations
- **Storage Objects**: 
  - `Object`: Abstract base class for persistent objects
  - `DiskObject`: Pickle-based disk storage
  - `CompressedDiskObject`: Zstd-compressed disk storage
  - `NetworkObject`: Real-time synchronized storage
- **FUSE Integration**: `BlockDeviceFUSE` class for filesystem mounting

## Development

### Setup
```bash
git clone https://github.com/Omena0/blockdevice.git
cd blockdevice
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=blockdevice --cov-report=html

# Run specific test file
pytest tests/test_utils.py
```

### Building
```bash
# Build the C++ extension
python setup.py build_ext --inplace

# Build distribution
python setup.py sdist bdist_wheel
```

## Examples

See the `examples/` directory for sample applications:

- `compressed.py`: Filesystem implementation with compression
- `network/`: Client-server examples

## API Reference

### BlockDevice
```python
BlockDevice(path: str, dolphin: bool = False)
```
Core block device operations.

### Storage Classes

#### DiskObject
```python
DiskObject(path: str, default_value=None)
```
Persistent dictionary stored as pickle file.

#### CompressedDiskObject
```python
CompressedDiskObject(path: str, default_value=None, compression_level=5)
```
Compressed persistent storage using zstd.

#### NetworkObject
```python
NetworkObject(host: str, port: int = None, default_value=None)
```
Real-time synchronized storage across network.

### FUSE
```python
BlockDeviceFUSE(block_device)
```
FUSE filesystem operations handler.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

See COPYING.md for license information.

## Authors

- Omena0 (omena0mc@gmail.com)
