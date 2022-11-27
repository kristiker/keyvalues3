import unittest
import io

from keyvalues3 import KV3File
from keyvalues3.binarywriter import BinaryV1UncompressedWriter
from keyvalues3.textreader import KV3TextReader

class TestBinaryV1UncompressedWriter(unittest.TestCase):
    
    def test_writes(self):
        with io.BytesIO() as file:
            writer = BinaryV1UncompressedWriter(KV3File({"A": 1}))
            writer.write(file)
    
    def test_write_match_expected(self):
        kv3_obj = KV3File({"A": 1})
        expect = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14t\x12\x16|\x06\xe9F\x98\xaf\xf2\xe6>\xb5\x907\xe7\x01\x00\x00\x00A\x00\t\x01\x00\x00\x00\x00\x00\x00\x00\r'
        with io.BytesIO() as file:
            writer = BinaryV1UncompressedWriter(kv3_obj)
            writer.write(file)
            file.seek(0)
            #print(file.read())
            self.assertEqual(file.read(), expect)
    
    def test_write_null(self):
        kv3_obj = KV3File(None)
        null_VKV = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14t\x12\x16|\x06\xe9F\x98\xaf\xf2\xe6>\xb5\x907\xe7\x00\x00\x00\x00\x01'
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
            with io.BytesIO() as file:
                writer = BinaryV1UncompressedWriter(kv3_obj)
                writer.write(file)
