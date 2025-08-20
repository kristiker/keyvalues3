"""
Test the resource parser functionality.
"""

import unittest
from pathlib import Path
import keyvalues3 as kv3
from tests.resource_parser import extract_kv3_from_resource
from keyvalues3.binaryreader import read_valve_keyvalue3, MemoryBuffer

class TestResourceParser(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = Path(__file__).parent
        self.resource_dir = self.test_dir / 'documents' / 'resource'
        self.binary_dir = self.test_dir / 'documents' / 'binary'
    
    def test_extract_kv3_from_mock_resource(self):
        """Test extracting KV3 data from mock resource files."""
        for resource_file in self.resource_dir.glob('*.vdata'):
            with self.subTest(file=resource_file.name):
                # Read the resource file
                resource_data = resource_file.read_bytes()
                
                # Extract KV3 data
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Verify it's valid KV3 data by parsing it
                buffer = MemoryBuffer(kv3_data)
                try:
                    result = read_valve_keyvalue3(buffer)
                    self.assertIsNotNone(result, f"Failed to parse extracted KV3 data from {resource_file.name}")
                except NotImplementedError:
                    # Some formats may not be implemented yet, that's expected
                    pass
                except Exception as e:
                    self.fail(f"Unexpected error parsing KV3 data from {resource_file.name}: {e}")
        
        # Also test more realistic .vrf files
        for resource_file in self.resource_dir.glob('*.vrf'):
            with self.subTest(file=resource_file.name):
                # Read the resource file
                resource_data = resource_file.read_bytes()
                
                # Extract KV3 data
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Verify it's valid KV3 data by parsing it
                buffer = MemoryBuffer(kv3_data)
                try:
                    result = read_valve_keyvalue3(buffer)
                    self.assertIsNotNone(result, f"Failed to parse extracted KV3 data from {resource_file.name}")
                except NotImplementedError:
                    # Some formats may not be implemented yet, that's expected
                    pass
                except Exception as e:
                    self.fail(f"Unexpected error parsing KV3 data from {resource_file.name}: {e}")
    
    def test_extract_from_raw_kv3_file(self):
        """Test that the parser handles raw KV3 files correctly."""
        for binary_file in self.binary_dir.glob('*.kv3'):
            with self.subTest(file=binary_file.name):
                # Read raw KV3 file
                kv3_data_original = binary_file.read_bytes()
                
                # Parse as if it were a resource file
                kv3_data_extracted = extract_kv3_from_resource(kv3_data_original)
                self.assertIsNotNone(kv3_data_extracted, f"Failed to handle raw KV3 file {binary_file.name}")
                
                # Should be identical
                self.assertEqual(kv3_data_original, kv3_data_extracted, 
                               f"Raw KV3 file {binary_file.name} was modified during extraction")
    
    def test_integration_with_main_api(self):
        """Test that extracted KV3 data works with the main API."""
        for resource_file in self.resource_dir.glob('*.vdata'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data)
                
                # Use with main API via BytesIO
                from io import BytesIO
                kv3_stream = BytesIO(kv3_data)
                
                try:
                    result = kv3.read(kv3_stream)
                    self.assertIsNotNone(result.value, f"Main API failed on extracted data from {resource_file.name}")
                except NotImplementedError:
                    # Some formats may not be implemented yet, that's ok
                    pass
                except Exception as e:
                    self.fail(f"Unexpected error with main API on {resource_file.name}: {e}")
        
        # Also test with .vrf files
        for resource_file in self.resource_dir.glob('*.vrf'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data)
                
                # Use with main API via BytesIO
                from io import BytesIO
                kv3_stream = BytesIO(kv3_data)
                
                try:
                    result = kv3.read(kv3_stream)
                    self.assertIsNotNone(result.value, f"Main API failed on extracted data from {resource_file.name}")
                except NotImplementedError:
                    # Some formats may not be implemented yet, that's ok
                    pass
                except Exception as e:
                    self.fail(f"Unexpected error with main API on {resource_file.name}: {e}")

if __name__ == '__main__':
    unittest.main()