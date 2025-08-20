"""
Simple Valve Resource Format parser utility for extracting KV3 data from resource files.

This is a minimal implementation that can extract DATA blocks containing binary KV3 data
from Valve Resource Format files for testing purposes.
"""

import struct
from io import BytesIO
from typing import Optional, Dict, Any

class ResourceBlock:
    """Represents a resource block with its metadata."""
    def __init__(self, block_type: str, offset: int, size: int, data: bytes):
        self.block_type = block_type
        self.offset = offset
        self.size = size
        self.data = data

class SimpleResourceParser:
    """
    A simple Valve Resource Format parser.
    
    This is not a complete implementation but is sufficient to extract
    KV3 data from resource files for testing purposes.
    """
    
    def __init__(self, data: bytes):
        self.data = data
        self.stream = BytesIO(data)
        self.blocks: Dict[str, ResourceBlock] = {}
        
    def parse(self) -> bool:
        """Parse the resource file and extract blocks."""
        try:
            # Check for various KV3 magic numbers first
            magic = self.stream.read(4)
            self.stream.seek(0)
            
            # Check if it's already a raw KV3 file with various magic numbers
            if magic in [b'VKV\x03', b'\x01VK3', b'\x023VK', b'\x033VK', b'\x043VK', b'\x053VK']:
                # This is already a raw KV3 file, create a fake DATA block
                self.blocks['DATA'] = ResourceBlock('DATA', 0, len(self.data), self.data)
                return True
            
            # Check for Valve Resource Format magic
            if magic == b'VKV3':
                # This is a mock resource file
                self.stream.seek(0)
                magic = self.stream.read(4)  # VKV3
                version = struct.unpack('<I', self.stream.read(4))[0]
                kv3_offset = struct.unpack('<I', self.stream.read(4))[0]
                kv3_size = struct.unpack('<I', self.stream.read(4))[0]
                
                # Read the KV3 data
                self.stream.seek(kv3_offset)
                kv3_data = self.stream.read(kv3_size)
                
                self.blocks['DATA'] = ResourceBlock('DATA', kv3_offset, kv3_size, kv3_data)
                return True
                
            return False
            
        except Exception:
            return False
            
    def get_kv3_data(self) -> Optional[bytes]:
        """Extract binary KV3 data from the resource file."""
        if 'DATA' in self.blocks:
            data = self.blocks['DATA'].data
            # Check if it's valid KV3 data with various magic numbers
            kv3_magics = [b'VKV\x03', b'\x01VK3', b'\x023VK', b'\x033VK', b'\x043VK', b'\x053VK']
            for magic in kv3_magics:
                if data.startswith(magic):
                    return data
        return None

def extract_kv3_from_resource(resource_data: bytes) -> Optional[bytes]:
    """
    Extract binary KV3 data from a Valve Resource Format file.
    
    Args:
        resource_data: Raw bytes of the resource file
        
    Returns:
        Binary KV3 data if found, None otherwise
    """
    parser = SimpleResourceParser(resource_data)
    if parser.parse():
        return parser.get_kv3_data()
    return None