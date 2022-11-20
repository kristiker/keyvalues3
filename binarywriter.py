import enum
import array
from typing import BinaryIO
from struct import pack
import keyvalues3 as kv3

class BinaryTypes(enum.IntEnum):
    string_multi = 0
    null = 1
    boolean = 2
    int64 = 3
    uint64 = 4
    double = 5
    string = 6
    binary_blob = 7
    array = 8
    dictionary = 9
    array_typed = 10
    int32 = 11
    uint32 = 12
    boolean_true = 13
    boolean_false = 14
    int64_zero = 15
    int64_one = 16
    double_zero = 17
    double_one = 18

simple_types = {
    None: BinaryTypes.null,
    True: BinaryTypes.boolean_true,
    False: BinaryTypes.boolean_false,
}

types = {
    int: BinaryTypes.int64,
    float: BinaryTypes.double,
    str: BinaryTypes.string,
    list: BinaryTypes.array,
    array.array: BinaryTypes.array_typed,
    dict: BinaryTypes.dictionary,
}

zeros_ones = {
    int: {
        0: BinaryTypes.int64_zero,
        1: BinaryTypes.int64_one,
    },
    float: {
        0.0: BinaryTypes.double_zero,
        1.0: BinaryTypes.double_one,
    },
}

class BinaryV1UncompressedWriter:
    def __init__(self, kv3file: kv3.KV3File, serialize_enums_as_ints: bool = False):
        self.kv3file = kv3file
        self.serialize_enums_as_ints = serialize_enums_as_ints

        self.strings: list[str] = []

    def __bytes__(self):
        # header
        data = bytearray(b"VKV\x03")
        data += kv3.binary.version.bytes
        data += self.kv3file.format.version.bytes
        
        # string table and object
        self.strings: list[str] = []
        object_serialized = self.object_and_type_serialize(self.kv3file.value)
        
        data += pack("<I", len(self.strings))
        for string in self.strings:
            data += string.encode("utf-8")
            data += b"\x00"
        
        return bytes(data + object_serialized)

    def write(self, file: BinaryIO):
        file.write(bytes(self))

    def object_and_type_serialize(self, object):
        flags = kv3.Flag(0)
        if isinstance(object, kv3.flagged_value):
            flags = object.flags
            object = object.value
        object_type = type(object)
        rv = bytearray()

        def pack_type_and_flags(type: BinaryTypes, flags: kv3.Flag):
            if flags == kv3.Flag(0):
                return pack("<B", type)
            return pack("<B", type | 0x80) + pack("<B", flags)

        try:
            if object in simple_types:
                rv += pack_type_and_flags(simple_types[object], flags)
                return rv
        except TypeError:
            pass

        if object_type in zeros_ones and object in zeros_ones[object_type]:
            rv += pack_type_and_flags(zeros_ones[object_type][object], flags)
            return rv

        type_in_binary = None
        if object_type in types:
            type_in_binary = types[object_type]
        elif isinstance(object, enum.IntEnum):
            type_in_binary = BinaryTypes.int32 if self.serialize_enums_as_ints else BinaryTypes.string
        else:
            raise TypeError(f"Unknown type {object_type}")
        rv += pack_type_and_flags(type_in_binary, flags)
        rv += self.object_serialize(object)
        return rv

    def object_serialize(self, object):
        rv = bytearray()
        match object:
            case bool():
                ...
            case enum.IntEnum():
                if self.serialize_enums_as_ints:
                    rv += pack("<i", object.value)
                else:
                    if object == "":
                        rv += pack("<i", -1)
                    else:
                        rv += pack("<i", len(self.strings))
                        self.strings.append(object)
            case int(): rv += pack("<q", object)
            case float(): rv += pack("<d", object)
            case str():
                if object == "":
                    rv += pack("<i", -1)
                else:
                    rv += pack("<i", len(self.strings))
                    self.strings.append(object)
            case list():
                rv += pack("<i", len(object))
                for item in object:
                    rv += self.object_and_type_serialize(item)
            case array.array(subType):
                rv += pack("<i", len(object))
                rv += pack("<B", BinaryTypes.int64)
                rv += pack("<B", kv3.Flag(0).value)
                for item in object:
                    rv += self.object_serialize(item)
            case dict():
                rv += pack("<i", len(object))
                for key, value in object.items():
                    rv += pack("<i", len(self.strings))
                    self.strings.append(key)
                    rv += self.object_and_type_serialize(value)
        return rv

if __name__ == "__main__":
    import unittest
    import io

    class TestBinaryV1UncompressedWriter(unittest.TestCase):
        
        def test_writes(self):
            with io.BytesIO() as file:
                writer = BinaryV1UncompressedWriter(kv3.KV3File({"A": 1}))
                writer.write(file)
        
        def test_write_match_expected(self):
            kv3_obj = kv3.KV3File({"A": 1})
            expect = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14t\x12\x16|\x06\xe9F\x98\xaf\xf2\xe6>\xb5\x907\xe7\x01\x00\x00\x00A\x00\t\x01\x00\x00\x00\x00\x00\x00\x00\r'
            with io.BytesIO() as file:
                writer = BinaryV1UncompressedWriter(kv3_obj)
                writer.write(file)
                file.seek(0)
                #print(file.read())
                self.assertEqual(file.read(), expect)
        
        def test_write_null(self):
            kv3_obj = kv3.KV3File(None)
            null_VKV = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14t\x12\x16|\x06\xe9F\x98\xaf\xf2\xe6>\xb5\x907\xe7\x00\x00\x00\x00\x01'
            with io.BytesIO() as file:
                writer = BinaryV1UncompressedWriter(kv3_obj)
                writer.write(file)
                file.seek(0)
                #print(file.read())
                self.assertEqual(file.read(), null_VKV)
        
        def test_writes_bt_config(self):
            with open("tests/bt_config.kv3", "r") as f:
                kv3_obj = kv3.KV3File.from_string(f.read())
                with io.BytesIO() as file:
                    writer = BinaryV1UncompressedWriter(kv3_obj)
                    writer.write(file)

    
    unittest.main()
