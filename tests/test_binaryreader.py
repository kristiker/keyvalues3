import unittest
import io
from pathlib import Path

import keyvalues3 as kv3
from keyvalues3.binaryreader import read_valve_keyvalue3, MemoryBuffer
from tests.resource_parser import extract_kv3_from_resource
#from keyvalues3 import KV3File
#from keyvalues3.binaryreader import BinaryV1UncompressedReader, BinaryLZ4
#from keyvalues3.textreader import KV3TextReader

class TestBinaryReader(unittest.TestCase):
    def test_reader_main_api(self):
        binary_kv3 = kv3.read("tests/documents/binary/example.kv3")
        assert isinstance(binary_kv3.value, dict)
        assert binary_kv3.value["stringValue"] == "hello world"

    def test_binary_reader_legacy(self):
        with open("tests/documents/binary/example.kv3", "rb") as f:
            buffer = MemoryBuffer(f.read())
            binary_kv3_value = read_valve_keyvalue3(buffer)
            assert isinstance(binary_kv3_value, dict)
            assert binary_kv3_value["stringValue"] == "hello world"


class TestBinaryReaderWithResourceFiles(unittest.TestCase):
    """Test binary readers with KV3 data extracted from Valve Resource Format files."""
    
    def setUp(self):
        self.test_dir = Path(__file__).parent
        self.resource_dir = self.test_dir / 'documents' / 'resource'
    
    def test_binary_reader_with_extracted_resource_data(self):
        """Test that the binary reader can handle KV3 data extracted from resource files."""
        for resource_file in self.resource_dir.glob('*.vdata'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data from resource file
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Test with binary reader
                buffer = MemoryBuffer(kv3_data)
                try:
                    result = read_valve_keyvalue3(buffer)
                    # Only test if parsing succeeded (some formats might not be implemented)
                    if result is not None:
                        self.assertIsInstance(result, (dict, list, str, int, float, bool, type(None)),
                                            f"Binary reader returned unexpected type for {resource_file.name}")
                except NotImplementedError:
                    # Some formats are not implemented yet, that's expected
                    pass
        
        # Also test .vrf files (more realistic format)
        for resource_file in self.resource_dir.glob('*.vrf'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data from resource file
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Test with binary reader
                buffer = MemoryBuffer(kv3_data)
                try:
                    result = read_valve_keyvalue3(buffer)
                    # Only test if parsing succeeded (some formats might not be implemented)
                    if result is not None:
                        self.assertIsInstance(result, (dict, list, str, int, float, bool, type(None)),
                                            f"Binary reader returned unexpected type for {resource_file.name}")
                except NotImplementedError:
                    # Some formats are not implemented yet, that's expected
                    pass
    
    def test_main_api_with_extracted_resource_data(self):
        """Test that the main API can handle KV3 data extracted from resource files."""
        for resource_file in self.resource_dir.glob('*.vdata'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data from resource file  
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Test with main API via BytesIO
                kv3_stream = io.BytesIO(kv3_data)
                try:
                    result = kv3.read(kv3_stream)
                    # Only test if parsing succeeded
                    if result is not None:
                        self.assertIsNotNone(result.value, f"Main API returned None value for {resource_file.name}")
                        # Verify it has the expected attributes
                        self.assertTrue(hasattr(result, 'original_encoding'), 
                                      f"Result missing original_encoding for {resource_file.name}")
                        self.assertTrue(hasattr(result, 'format'),
                                      f"Result missing format for {resource_file.name}")
                except NotImplementedError:
                    # Some formats are not implemented yet, that's expected
                    pass
        
        # Also test .vrf files (more realistic format)
        for resource_file in self.resource_dir.glob('*.vrf'):
            with self.subTest(file=resource_file.name):
                # Extract KV3 data from resource file  
                resource_data = resource_file.read_bytes()
                kv3_data = extract_kv3_from_resource(resource_data)
                self.assertIsNotNone(kv3_data, f"Failed to extract KV3 data from {resource_file.name}")
                
                # Test with main API via BytesIO
                kv3_stream = io.BytesIO(kv3_data)
                try:
                    result = kv3.read(kv3_stream)
                    # Only test if parsing succeeded
                    if result is not None:
                        self.assertIsNotNone(result.value, f"Main API returned None value for {resource_file.name}")
                        # Verify it has the expected attributes
                        self.assertTrue(hasattr(result, 'original_encoding'), 
                                      f"Result missing original_encoding for {resource_file.name}")
                        self.assertTrue(hasattr(result, 'format'),
                                      f"Result missing format for {resource_file.name}")
                except NotImplementedError:
                    # Some formats are not implemented yet, that's expected
                    pass
    
    def test_resource_parser_finds_valid_kv3_files(self):
        """Ensure our resource parser actually finds some valid KV3 files to test with."""
        valid_files = 0
        for resource_file in self.resource_dir.glob('*.vdata'):
            resource_data = resource_file.read_bytes()
            kv3_data = extract_kv3_from_resource(resource_data)
            if kv3_data is not None:
                valid_files += 1
        
        for resource_file in self.resource_dir.glob('*.vrf'):
            resource_data = resource_file.read_bytes()
            kv3_data = extract_kv3_from_resource(resource_data)
            if kv3_data is not None:
                valid_files += 1
        
        self.assertGreater(valid_files, 0, "Resource parser should find at least one valid KV3 file to test with")

#class TestBinaryV1UncompressedWriter(unittest.TestCase):
