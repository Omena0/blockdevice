from abc import ABC, abstractmethod
import threading
import pickle
import socket
import base64
import zstd
import os

class Object(ABC):
    """Abstract base class for objects that can save and load their state."""
    
    def __init__(self, default_value=None):
        self._data = default_value if default_value is not None else {}

    @abstractmethod
    def load(self):
        """Load data from storage"""
        pass

    @abstractmethod
    def save(self):
        """Save data to storage"""
        pass

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value
        self.save()

    def __delitem__(self, key):
        del self._data[key]
        self.save()

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def pop(self, key, *args):
        result = self._data.pop(key, *args)
        self.save()
        return result

    def clear(self):
        self._data.clear()
        self.save()

    def update(self, other):
        self._data.update(other)
        self.save()

class DiskObject(Object):
    """
    A object that mirrors its state to a file and loads it on creation.
    Supports dict-like, list-like, and general object behavior.
    """

    def __init__(self, path, default_value=None):
        self.path = path
        super().__init__(default_value)
        self.load()

    def load(self):
        """Load data from disk"""
        try:
            with open(self.path, 'rb') as f:
                self._data = self._deserialize(f.read())
        except (FileNotFoundError, EOFError, pickle.UnpicklingError):
            self._data = {}

    def save(self):
        """Save data to disk"""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'wb') as f:
            f.write(self._serialize(self._data))

    def _serialize(self, data):
        """Serialize data - can be overridden by subclasses"""
        return pickle.dumps(data)

    def _deserialize(self, data):
        """Deserialize data - can be overridden by subclasses"""
        return pickle.loads(data)

    def __repr__(self):
        return f"{type(self).__name__}(path='{self.path}', data={repr(self._data)})"

class CompressedDiskObject(DiskObject):
    """
    A DiskObject that compresses its data using zstd with compression level 5.
    """

    def __init__(self, path, default_value=None, compression_level=5):
        # Set compression_level as a private attribute first to avoid recursion
        object.__setattr__(self, 'compression_level', compression_level)
        super().__init__(path, default_value)

    def _serialize(self, data):
        """Serialize and compress data"""
        pickled_data = pickle.dumps(data)
        return zstd.compress(pickled_data, self.compression_level)

    def _deserialize(self, data):
        """Decompress and deserialize data"""
        decompressed_data = zstd.decompress(data)
        return pickle.loads(decompressed_data)

class NetworkObject(Object):
    """Simple real-time synchronized object using basic TCP protocol."""
    
    def __init__(self, host, port=None, default_value=None):
        if isinstance(host, str) and ':' in host and port is None:
            host, port = host.rsplit(':', 1)
            port = int(port)
        elif port is None:
            raise ValueError("Port must be specified")
        
        self.host = host
        self.port = int(port)
        self._server_socket = None
        self._client_socket = None
        self._clients = set()
        self._is_server = False
        self._running = True
        self._data = default_value if default_value is not None else {}
        
        # Try to connect as client
        try:
            self._connect_client()
        except ConnectionError:
            pass  # Will be server instead
    
    def _connect_client(self):
        """Connect to server as client"""
        self._client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._client_socket.settimeout(5.0)  # Only for connection
        self._client_socket.connect((self.host, self.port))
        self._client_socket.settimeout(None)  # Remove timeout after connection
        
        # Start listener thread
        threading.Thread(target=self._client_listener, daemon=True).start()
    
    def _client_listener(self):
        """Listen for data updates from server"""
        buffer = b""
        while self._running and self._client_socket:
            try:
                chunk = self._client_socket.recv(1024)
                if not chunk:
                    break
                
                buffer += chunk
                
                # Process complete messages
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line.startswith(b'DATA:'):
                        try:
                            data_b64 = line[5:]  # Remove "DATA:"
                            data = pickle.loads(base64.b64decode(data_b64))
                            self._data = data
                        except Exception as e:
                            print(f"Failed to decode data: {e}")
                            
            except Exception as e:
                print(f"Client listener error: {e}")
                break
        
        # Cleanup
        if self._client_socket:
            try:
                self._client_socket.close()
            except:
                pass
            self._client_socket = None
    
    def _handle_client(self, client_socket):
        """Handle a connected client"""
        self._clients.add(client_socket)
        
        # Send current data immediately
        if self._data:
            self._send_data(client_socket, self._data)
        
        # Keep connection alive and listen for client updates
        buffer = b""
        try:
            while self._running:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                
                buffer += chunk
                
                # Process complete messages
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if line.startswith(b'DATA:'):
                        try:
                            data_b64 = line[5:]
                            data = pickle.loads(base64.b64decode(data_b64))
                            self._data = data
                            # Broadcast to all other clients
                            self._broadcast_data(data, exclude=client_socket)
                        except Exception as e:
                            print(f"Failed to decode client data: {e}")
        except Exception as e:
            print(f"Client handler error: {e}")
        finally:
            self._clients.discard(client_socket)
            try:
                client_socket.close()
            except:
                pass
    
    def _send_data(self, sock, data):
        """Send data to a socket"""
        try:
            pickled = pickle.dumps(data)
            b64_data = base64.b64encode(pickled)
            message = b'DATA:' + b64_data + b'\n'
            sock.sendall(message)
        except Exception as e:
            print(f"Failed to send data: {e}")
    
    def _broadcast_data(self, data, exclude=None):
        """Broadcast data to all clients except excluded one"""
        dead_clients = set()
        for client in self._clients.copy():
            if client != exclude:
                try:
                    self._send_data(client, data)
                except:
                    dead_clients.add(client)
        
        # Remove dead clients
        self._clients -= dead_clients
        for client in dead_clients:
            try:
                client.close()
            except:
                pass
    
    def serve(self):
        """Start as server"""
        if self._is_server:
            return
        
        self._is_server = True
        
        # Close client connection if exists
        if self._client_socket:
            self._client_socket.close()
            self._client_socket = None
        
        # Start server
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(10)
        
        while self._running and self._server_socket:
            try:
                client_socket, addr = self._server_socket.accept()
                threading.Thread(
                    target=self._handle_client, 
                    args=(client_socket,), 
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Server accept error: {e}")
                break
    
    def load(self):
        """No-op for network objects"""
        pass
    
    def save(self):
        """Save by sending to server or broadcasting if server"""
        if self._is_server:
            # Broadcast to all clients
            self._broadcast_data(self._data)
        elif self._client_socket:
            # Send to server
            self._send_data(self._client_socket, self._data)
        # If no connection, data is just stored locally

