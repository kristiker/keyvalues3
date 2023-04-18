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
        with self.assertRaises(ValueError): Format('vpcf', "v2")
        with self.assertRaises(ValueError): Format('vpcf1 with spaces', uuid.UUID(int = 0))

    def test_empty_instantiated_kv3file_is_null(self):
        kv3_null_implicit = KV3File()
        kv3_null = KV3File(None)
        assert kv3_null_implicit.value is None
        assert kv3_null.value is None

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
        textwriter.encode(KV3File(value=None))
        textwriter.encode(KV3File(value=True))
        textwriter.encode(KV3File(value=False))
        textwriter.encode(KV3File(value=1))
        textwriter.encode(KV3File(value=1.0))
        textwriter.encode(KV3File(value=self.MyKV3Format.Substance.FIRE))
        textwriter.encode(KV3File(value=str()))
        textwriter.encode(KV3File(value=flagged_value(str(), Flag.multilinestring)))
        textwriter.encode(KV3File(value=flagged_value(str(), Flag.resource)))
        textwriter.encode(KV3File(value=[]))
        textwriter.encode(KV3File(value={}))
        textwriter.encode(KV3File(value=self.MyKV3Format(), format=self.MyKV3Format.format))
        textwriter.encode(KV3File(value=bytes(byte for byte in range(256))))
        textwriter.encode(KV3File(value=bytearray(byte for byte in range(256))))

    def test_dict_proxy(self):
        usual_kv3 = KV3File(value={'_class': 'CParticleSystemDefinition', 'b': 2, 'c': 3})
        list_based_kv3 = KV3File(value=["a", "b", "c"])
        leet_kv3 = KV3File(value=1337)

        self.assertEqual(usual_kv3['_class'], "CParticleSystemDefinition")

        self.assertSetEqual(set(usual_kv3.keys()), {'_class', 'b', 'c'})
        self.assertSetEqual(set(usual_kv3.values()), {'CParticleSystemDefinition', 2, 3})

        self.assertEqual(repr([*usual_kv3.keys()]), "['_class', 'b', 'c']")
        self.assertEqual(repr([*usual_kv3.values()]), "['CParticleSystemDefinition', 2, 3]")

        self.assertEqual(repr(usual_kv3.keys()), "dict_keys(['_class', 'b', 'c'])")
        self.assertEqual(repr(usual_kv3.values()), "dict_values(['CParticleSystemDefinition', 2, 3])")

        with self.assertRaises(TypeError) as exception: list_based_kv3['a']
        with self.assertRaises(TypeError) as exception: list_based_kv3[1]
        with self.assertRaises(TypeError) as exception: list_based_kv3.keys()

        self.assertTrue("KV3 root value is of type 'list'" in str(exception.exception))
    
        with self.assertRaises(TypeError) as exception: reversed(usual_kv3)
        with self.assertRaises(TypeError) as exception: reversed(list_based_kv3)

        null_kv3 = KV3File()
        with self.assertRaises(TypeError): null_kv3["my"] = "value"
        with self.assertRaises(TypeError): null_kv3["my"]
        with self.assertRaises(TypeError): del null_kv3["my"]
        with self.assertRaises(TypeError): len(null_kv3)
        with self.assertRaises(TypeError): iter(null_kv3)

        def pattern_match(v) -> str:
            match v:
                case KV3File(value={ '_class': 'CParticleSystemDefinition'}): return "particle system!"
                case KV3File(value=list()): return "list based kv3"
                case KV3File(value=None): return "null kv3"
                case KV3File(value=1337): return "leet kv3"
                case KV3File(): return "any other kv3"
                case _: return "none of these"

        self.assertEqual(pattern_match(usual_kv3), "particle system!")
        self.assertEqual(pattern_match(list_based_kv3), "list based kv3")
        self.assertEqual(pattern_match(leet_kv3), "leet kv3")
        self.assertEqual(pattern_match(null_kv3), "null kv3")

        self.assertEqual(pattern_match(KV3File("asd")), "any other kv3")
