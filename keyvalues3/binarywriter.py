import enum
import array
from typing import BinaryIO
from struct import pack
from . import keyvalues3 as kv3

class BinaryTypes(enum.IntEnum):
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

types = {
    int: BinaryTypes.int64,
    float: BinaryTypes.double,
    str: BinaryTypes.string,
    list: BinaryTypes.array,
    array.array: BinaryTypes.array_typed,
    bytes: BinaryTypes.binary_blob,
    bytearray: BinaryTypes.binary_blob,
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
    encoding = kv3.KV3_ENCODING_BINARY_UNCOMPRESSED
    def __init__(self, kv3file: kv3.KV3File, serialize_enums_as_ints: bool = False):
        self.kv3file = kv3file
        self.serialize_enums_as_ints = serialize_enums_as_ints

        self.strings: dict[str, int] = {}

    def __bytes__(self) -> bytes:
        self.strings.clear()
        return bytes(self.encode_header() + self.encode_body())

    def encode_header(self):
        return b"VKV\x03" + self.encoding.version.bytes_le + self.kv3file.format.version.bytes_le

    def encode_body(self) -> bytes:
        object_serialized = self.object_and_type_serialize(self.kv3file.value)
        string_table = self.encode_strings()
        return string_table + object_serialized + b"\xFF\xFF\xFF\xFF"

    def encode_strings(self):
        string_table = pack("<I", len(self.strings))
        for string in self.strings:
            string_table += string.encode("utf-8")
            string_table += b"\x00"
        return string_table

    def write(self, file: BinaryIO):
        file.write(bytes(self))

    def object_and_type_serialize(self, object) -> bytes:
        flags = kv3.Flag(0)
        if isinstance(object, kv3.flagged_value):
            flags = object.flags
            object = object.value
        object_type = type(object)

        def pack_type_and_flags(type: BinaryTypes, flags: kv3.Flag):
            if flags == kv3.Flag(0):
                return pack("<B", type)
            return pack("<B", type | 0x80) + pack("<B", flags)

        if object is None: return pack_type_and_flags(BinaryTypes.null, flags)
        if object is True: return pack_type_and_flags(BinaryTypes.boolean_true, flags)
        if object is False: return pack_type_and_flags(BinaryTypes.boolean_false, flags)

        if object_type in zeros_ones and object in zeros_ones[object_type]:
            return pack_type_and_flags(zeros_ones[object_type][object], flags)

        type_in_binary = None
        if object_type in types:
            type_in_binary = types[object_type]
        elif isinstance(object, enum.IntEnum):
            type_in_binary = BinaryTypes.int32 if self.serialize_enums_as_ints else BinaryTypes.string
        else:
            if isinstance(object, list):
                type_in_binary = BinaryTypes.array
            else:
                raise TypeError(f"Unknown type {object_type}")

        return pack_type_and_flags(type_in_binary, flags) + self.object_serialize(object)

    def object_serialize(self, object) -> bytearray:
        rv = bytearray()
        match object:
            case bool():
                ...
            case enum.IntEnum():
                if self.serialize_enums_as_ints:
                    rv += pack("<i", object.value)
                else:
                    rv += pack("<i", self.register_string_to_table(object))
            case int(): rv += pack("<q", object)
            case float(): rv += pack("<d", object)
            case str():
                rv += pack("<i", self.register_string_to_table(object))
            case list():
                rv += pack("<i", len(object))
                for item in object:
                    rv += self.object_and_type_serialize(item)
            case array.array():
                rv += pack("<i", len(object))
                rv += pack("<B", BinaryTypes.int64)
                rv += pack("<B", kv3.Flag(0).value)
                for item in object:
                    rv += self.object_serialize(item)
            case bytes() | bytearray():
                rv += pack("<i", len(object))
                rv += object
            case dict():
                rv += pack("<i", len(object))
                for key, value in object.items():
                    rv += pack("<i", self.register_string_to_table(key))
                    rv += self.object_and_type_serialize(value)
        return rv

    def register_string_to_table(self, object):
        if object == "":
            return -1
        return self.strings.setdefault(object, len(self.strings))


import lz4.block
class BinaryLZ4(BinaryV1UncompressedWriter):
    encoding = kv3.KV3_ENCODING_BINARY_BLOCK_LZ4
    def __bytes__(self):
        self.strings.clear()
        rv = self.encode_header()
        body_uncompressed = self.encode_body()
        rv += pack("<I", len(body_uncompressed))
        rv += lz4.block.compress(body_uncompressed, store_size=False)
        return rv
