import unittest
import io

import keyvalues3 as kv3
from keyvalues3.binaryreader import read_valve_keyvalue3
from keyvalues3.utils import MemoryBuffer
#from keyvalues3 import KV3File
#from keyvalues3.binaryreader import BinaryV1UncompressedReader, BinaryLZ4
#from keyvalues3.textreader import KV3TextReader

class TestBinaryReader(unittest.TestCase):
    def test_reader_main_api(self):
        binary_kv3 = kv3.read("tests/documents/binary/legacy.kv3.bin")
        assert isinstance(binary_kv3.value, dict)
        assert binary_kv3.value["stringValue"] == "hello world"

    def test_binary_reader_legacy(self):
        with open("tests/documents/binary/legacy.kv3.bin", "rb") as f:
            buffer = MemoryBuffer(f.read())
            binary_kv3_value = read_valve_keyvalue3(buffer)
            assert isinstance(binary_kv3_value, dict)
            assert binary_kv3_value["stringValue"] == "hello world"

#class TestBinaryV1UncompressedWriter(unittest.TestCase):
