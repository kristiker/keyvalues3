import unittest
import io

import keyvalues3 as kv3
#from keyvalues3 import KV3File
#from keyvalues3.binaryreader import BinaryV1UncompressedReader, BinaryLZ4
#from keyvalues3.textreader import KV3TextReader

class TestBinaryReader(unittest.TestCase):
    def test_reader_main_api(self):
        binary_kv3 = kv3.read("tests/documents/binary/example.kv3")
        assert isinstance(binary_kv3.value, dict)
        assert binary_kv3.value["binary"] == "reader2"

#class TestBinaryV1UncompressedWriter(unittest.TestCase):
