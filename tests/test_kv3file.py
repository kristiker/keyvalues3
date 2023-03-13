import unittest

import enum
import dataclasses
import uuid
from keyvalues3 import KV3File, KV3Header, Encoding, Format, Flag, flagged_value, is_valid, check_valid, textwriter

class Test_KV3File(unittest.TestCase):
    default_header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
    def test_default_header(self):
        self.assertEqual(str(KV3Header()), self.default_header)

    def test_custom_header(self):
        self.assertEqual(
            str(KV3Header(Encoding('text2', uuid.UUID(int = 0)), Format('generic2', uuid.UUID(int = 1)))),
            '<!-- kv3 encoding:text2:version{00000000-0000-0000-0000-000000000000} format:generic2:version{00000000-0000-0000-0000-000000000001} -->'
        )

        with self.assertRaises(ValueError): Format('vpcf', "v2")
        with self.assertRaises(ValueError): Format('vpcf1 with spaces', uuid.UUID(int = 0))

    def test_empty_instantiated_kv3file(self):
        self.assertEqual(
            textwriter.write(KV3File()),
            self.default_header + "\nnull"
        )
        self.assertEqual(
            textwriter.write(KV3File(), textwriter.TextWriterOptions(no_header=True)),
            "null"
        )

    def test_dataclass_instantiated_kv3file(self):
        @dataclasses.dataclass
        class MyKV3Format:
            a: str = 'asd asd'
            b: dict = dataclasses.field(default_factory=lambda: {"inner_b":3})
            c: list = dataclasses.field(default_factory=lambda: ["listed_text1", "listed_text2"])
        self.assertEqual(
            textwriter.write_text(KV3File(MyKV3Format())),
            self.default_header + "\n" + """
            {
                a = "asd asd"
                b = 
                {
                    inner_b = 3
                }
                c = ["listed_text1", "listed_text2"]
            }
            """.strip() # undo detached triple quotes
            .replace(" "*4, "\t") # convert to tabs
            .replace("\t"*3, "") # remove added indent
        )

    def test_dict_instantiated_kv3file(self):
        self.assertEqual(
            textwriter.write_text(KV3File({
                'a': 'asd asd',
                'b': {
                    "inner_b": 3
                },
                'c': ["listed_text1", "listed_text2"]
            }
            )),
            self.default_header + "\n" + """
            {
                a = "asd asd"
                b = 
                {
                    inner_b = 3
                }
                c = ["listed_text1", "listed_text2"]
            }
            """.strip() # undo detached triple quotes
            .replace(" "*4, "\t") # convert to tabs
            .replace("\t"*3, "") # remove added indent
        )

class Test_KV3Value(unittest.TestCase):
    
    @dataclasses.dataclass
    class MyKV3Format:
        format = Format('mycustomformat', uuid.uuid4())
        class Substance(enum.IntEnum):
            WATER = 0
            FIRE = 1
        substance: Substance = Substance.WATER

    def test_kv3_value_validity(self):
        with self.assertRaises(TypeError):  check_valid(value=(5, 6, 7))
        with self.assertRaises(TypeError):  check_valid(value=flagged_value(set(), Flag(1)))
        with self.assertRaises(ValueError): check_valid(value={"key with space": 5})
        self.assertTrue(is_valid(value=None))
        self.assertTrue(is_valid(value=True))
        self.assertTrue(is_valid(value=False))
        self.assertTrue(is_valid(value=1))
        self.assertTrue(is_valid(value=1.0))
        self.assertTrue(is_valid(value=self.MyKV3Format.Substance.FIRE))
        self.assertTrue(is_valid(value=str()))
        self.assertTrue(is_valid(value=flagged_value(str(), Flag.multilinestring)))
        self.assertTrue(is_valid(value=[]))
        self.assertTrue(is_valid(value={}))
        self.assertTrue(is_valid(value=bytes(byte for byte in range(256))))
        self.assertTrue(is_valid(value=bytearray(byte for byte in range(256))))

        #self.assertFalse(is_valid(float('inf')))
        self.assertFalse(is_valid(2**64))
        self.assertFalse(is_valid(-1 + -2**63))
        self.assertFalse(is_valid({"key with space": 5}))
        self.assertFalse(is_valid([set(), set(), set()]))
        self.assertFalse(is_valid(KV3File))
        self.assertFalse(is_valid(KV3File()))

    def test_self_referencing_list_throws(self):
        l = []
        l.append(l)
        with self.assertRaises(ValueError):
            check_valid(l)

    def test_self_referencing_dict_throws(self):
        d = {}
        d['dub'] = d
        with self.assertRaises(ValueError):
            check_valid(d)
    
    def test_flagged_value_equality(self):
        self.assertEqual(flagged_value("multi\nline\nstring", Flag.multilinestring), "multi\nline\nstring")
        self.assertEqual(flagged_value(9999), 9999)
        self.assertEqual(flagged_value(5, Flag.resource), flagged_value(5, Flag.resource))

        self.assertNotEqual(flagged_value(5, Flag.resource), flagged_value(5, Flag.resource_name))
        self.assertNotEqual(flagged_value(5, Flag.resource), flagged_value(9999, Flag.resource))
        self.assertNotEqual(flagged_value(5, Flag.resource), flagged_value(9999, Flag.resource_name))
        self.assertNotEqual(flagged_value(5, Flag.resource), flagged_value(5, Flag.resource | Flag.resource_name))

    def test_value_serializes(self):
        textwriter.write_text(KV3File(value=None))
        textwriter.write_text(KV3File(value=True))
        textwriter.write_text(KV3File(value=False))
        textwriter.write_text(KV3File(value=1))
        textwriter.write_text(KV3File(value=1.0))
        textwriter.write_text(KV3File(value=self.MyKV3Format.Substance.FIRE))
        textwriter.write_text(KV3File(value=str()))
        textwriter.write_text(KV3File(value=flagged_value(str(), Flag.multilinestring)))
        textwriter.write_text(KV3File(value=flagged_value(str(), Flag.resource)))
        textwriter.write_text(KV3File(value=[]))
        textwriter.write_text(KV3File(value={}))
        textwriter.write_text(KV3File(value=self.MyKV3Format(), format=self.MyKV3Format.format))
        textwriter.write_text(KV3File(value=bytes(byte for byte in range(256))))
        textwriter.write_text(KV3File(value=bytearray(byte for byte in range(256))))
