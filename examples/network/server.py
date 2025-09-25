import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from blockdevice.utils import NetworkObject

fs = NetworkObject('127.0.0.1', 8080, {'/': {"type": "dir", "contents": []}})

fs.serve()
