import unittest
import io

from keyvalues3 import KV3File
from keyvalues3.binarywriter import BinaryV1UncompressedWriter, BinaryLZ4
from keyvalues3.textreader import KV3TextReader

class TestBinaryV1UncompressedWriter(unittest.TestCase):
    
    def test_empty_string_table(self):
        writer = BinaryV1UncompressedWriter(None)
        self.assertEqual(writer.encode_strings(), b'\x00\x00\x00\x00')

    def test_encodes(self):
        bytes(BinaryV1UncompressedWriter(KV3File({"A": 1})))

    def test_writes(self):
        with io.BytesIO() as file:
            writer = BinaryV1UncompressedWriter(KV3File({"A": 1}))
            writer.write(file)
    
    def test_write_match_expected(self):
        kv3_obj = KV3File({"A": 1})
        expect = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14|\x16\x12t\xe9\x06\x98F\xaf\xf2\xe6>\xb5\x907\xe7\x01\x00\x00\x00A\x00\t\x01\x00\x00\x00\x00\x00\x00\x00\x10\xFF\xFF\xFF\xFF'
        with io.BytesIO() as file:
            writer = BinaryV1UncompressedWriter(kv3_obj)
            writer.write(file)
            file.seek(0)
            #print(file.read())
            self.assertEqual(file.read(), expect)
    
    def test_write_null(self):
        kv3_obj = KV3File(None)
        null_VKV = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14|\x16\x12t\xe9\x06\x98F\xaf\xf2\xe6>\xb5\x907\xe7\x00\x00\x00\x00\x01\xFF\xFF\xFF\xFF'
        with io.BytesIO() as file:
            writer = BinaryV1UncompressedWriter(kv3_obj)
            writer.write(file)
            file.seek(0)
            #print(file.read())
            self.assertEqual(file.read(), null_VKV)
    
    def test_writes_bt_config(self):
        try:
            with open("tests/documents/bt_config.kv3", "r") as f:
                kv3_obj = KV3TextReader().parse(f.read())
        except Exception:
            self.skipTest("text parser fail, unrelated to binary writer")
        else:
            with io.BytesIO() as f:
                writer = BinaryV1UncompressedWriter(kv3_obj)
                writer.write(f)

class TestBinaryLZ4:
    def test_encodes(self):
        bytes(BinaryLZ4(KV3File({"A": 1})))
