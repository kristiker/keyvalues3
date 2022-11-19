import dataclasses
import enum
from typing import Protocol, runtime_checkable
from uuid import UUID

@dataclasses.dataclass(frozen=True)
class _HeaderPiece:
    name: str
    version: UUID
    def __post_init__(self):
        if not self.name.isidentifier():
            raise ValueError(f"{self!r}: name is not a valid identifier")
        if not isinstance(self.version, UUID):
            self.version = UUID(hex=self.version)
    def __str__(self):
        return "%s:%s:version{%s}" % (self.__class__.__name__.lower(), self.name, str(self.version))

@dataclasses.dataclass(frozen=True)
class Encoding(_HeaderPiece): pass
@dataclasses.dataclass(frozen=True)
class Format(_HeaderPiece): pass

text = Encoding("text", UUID("e21c7f3c-8a33-41c5-9977-a76d3a32aa0d"))
generic = Format("generic", UUID("7412167c-06e9-4698-aff2-e63eb59037e7"))

@dataclasses.dataclass(frozen=True)
class KV3Header:
    encoding: Encoding = text
    format: Format = generic
    def __str__(self):
        return f"<!-- kv3 {self.encoding} {self.format} -->\n"

class str_multiline(str):
    pass

simple_types = None | bool | int | float | enum.IntEnum | str | str_multiline
container_types = list[simple_types] | dict[str, simple_types]
bytearrays = bytes | bytearray
kv3_types = simple_types | container_types | bytearrays

def check_valid(value: kv3_types):
    match value:
        case flagged_value(actual_value, _):
            return check_valid(actual_value)
        case None | bool() | float() | enum.IntEnum() | str() | str_multiline():
            pass
        case int():
            if value > 2**64 - 1: raise OverflowError("int value is bigger than biggest UInt64")
            elif value < -2**63: raise OverflowError("int value is smaller than smallest Int64")
        case list():
            for nested_value in value:
                if nested_value is value:
                    raise ValueError("list contains itself")
                check_valid(nested_value)
        case dict():
            for key, nested_value in value.items():
                if nested_value is value:
                    raise ValueError("dict contains itself")
                if not isinstance(key, str):
                    raise ValueError("dict key is not a string")
                if not key.isidentifier():
                    raise ValueError("dict key is not a valid identifier") # I think
                check_valid(nested_value)
        case bytes() | bytearray():
            pass
        case _:
            raise TypeError("Invalid type for KV3 value.")

def is_valid(value: kv3_types) -> bool:
    try:
        check_valid(value)
        return True
    except (ValueError, OverflowError, TypeError):
        return False

@enum.global_enum
class Flag(enum.Flag):
    resource = enum.auto()
    resourcename = enum.auto()
    panorama = enum.auto()
    soundevent = enum.auto()
    subclass = enum.auto()
    def __str__(self):
        return "+".join(flag.name for flag in self.__class__ if self.value & flag)
    def __call__(self, value: kv3_types):
        return flagged_value(value, self)

@dataclasses.dataclass(slots=True)
class flagged_value:
    value: kv3_types
    flags: Flag = Flag(0)

kv3_types = kv3_types | flagged_value

@runtime_checkable
class Dataclass(Protocol):
    __dataclass_fields__: dict[str, dataclasses.Field]

class KV3File:
    def __init__(self,
            value: kv3_types | Dataclass = None,
            format: Format = generic,
            validate_value: bool = False,
            serialize_enums_as_ints: bool = False,
            ):

        self.header = KV3Header(format=format)

        match value:
            case Dataclass():
                self.value = dataclasses.asdict(value)
            case _:
                self.value = value

        if validate_value:
            check_valid(self.value)

        self.serialize_enums_as_ints = serialize_enums_as_ints

    def __str__(self):
        kv3 = str(self.header)
        def obj_serialize(obj, indent = 1, dictObj = False):
            preind = ('\t' * (indent-1))
            ind = ('\t' * indent)
            match obj:
                case flagged_value(value, flags):
                    if flags:
                        return f"{flags}:{obj_serialize(value)}"
                    return obj_serialize(value)
                case None:
                    return 'null'
                case False:
                    return 'false'
                case True:
                    return 'true'
                case int():
                    return str(obj)
                case float():
                    return str(round(obj, 6))
                case enum.IntEnum():
                    if self.serialize_enums_as_ints:
                        return str(obj.value)
                    return obj.name
                case str():
                    return '"' + obj + '"'
                case str_multiline():
                    return '"""' + obj + '"""'
                case list():
                    s = '['
                    if any(isinstance(item, dict) for item in obj):  # TODO: only non numbers
                        s = f'\n{preind}[\n'
                        for item in obj:
                            s += (obj_serialize(item, indent+1) + ',\n')
                        return s + preind + ']\n'

                    return f'[{", ".join((obj_serialize(item, indent+1) for item in obj))}]'
                case dict():
                    s = preind + '{\n'
                    if dictObj:
                        s = '\n' + s
                    for key, value in obj.items():
                        if not isinstance(key, str):
                            key = f'"{key}"'
                        s +=  ind + f"{key} = {obj_serialize(value, indent+1, dictObj=True)}\n"
                    return s + preind + '}'
                case bytes() | bytearray():
                    return f"#[{' '.join(f'{b:02x}' for b in obj)}]"
                case _:
                    raise TypeError("Invalid type for KV3 value.")

        kv3 += obj_serialize(self.value)

        return kv3

    def ToString(self): return self.__str__()

    def __bytes__(self):
        ...

if __name__ == '__main__':
    import unittest
    class Test_KV3File(unittest.TestCase):
        default_header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n'
        def test_default_header(self):
            self.assertEqual(str(KV3Header()), self.default_header)

        def test_custom_header(self):
            self.assertEqual(
                str(KV3Header(Encoding('text2', UUID(int = 0)), Format('generic2', UUID(int = 1)))),
                '<!-- kv3 encoding:text2:version{00000000-0000-0000-0000-000000000000} format:generic2:version{00000000-0000-0000-0000-000000000001} -->\n'
            )

            with self.assertRaises(ValueError): Format('vpcf', "v2")
            with self.assertRaises(ValueError): Format('vpcf1 with spaces', UUID(int = 0))

        def test_empty_instantiated_kv3file(self):
            self.assertEqual(
                KV3File().ToString(),
                self.default_header + "null"
            )

        def test_dataclass_instantiated_kv3file(self):
            @dataclasses.dataclass
            class MyKV3Format:
                a: str = 'asd asd'
                b: dict = dataclasses.field(default_factory=lambda: {"inner_b":3})
                c: list = dataclasses.field(default_factory=lambda: ["listed_text1", "listed_text2"])
            self.assertEqual(
                KV3File(MyKV3Format()).ToString(),
                self.default_header + """
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
                .replace("\t"*4, "") # remove added indent
            )

        def test_dict_instantiated_kv3file(self):
            self.assertEqual(
                KV3File({
                    'a': 'asd asd',
                    'b': {
                        "inner_b": 3
                    },
                    'c': ["listed_text1", "listed_text2"]
                }
                ).ToString(),
                self.default_header + """
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
                .replace("\t"*4, "") # remove added indent
            )

    class Test_KV3Value(unittest.TestCase):
        class MyKV3IntEnum(enum.IntEnum):
            WATER = 0
            FIRE = 1
        def test_kv3_value_validity(self):
            with self.assertRaises(TypeError):  check_valid(value=tuple(5, 6, 7))
            with self.assertRaises(TypeError):  check_valid(value=flagged_value(set(), Flag(1)))
            with self.assertRaises(ValueError): check_valid(value={"key with space": 5})
            self.assertTrue(is_valid(value=None))
            self.assertTrue(is_valid(value=True))
            self.assertTrue(is_valid(value=False))
            self.assertTrue(is_valid(value=1))
            self.assertTrue(is_valid(value=1.0))
            self.assertTrue(is_valid(value=self.MyKV3IntEnum.FIRE))
            self.assertTrue(is_valid(value=str()))
            self.assertTrue(is_valid(value=str_multiline()))
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

        def test_self_ref_list_value_throws(self):
            l = []
            l.append(l)
            with self.assertRaises(ValueError):
                check_valid(l)

        def test_self_ref_dict_value_throws(self):
            d = {}
            d['dub'] = d
            with self.assertRaises(ValueError):
                check_valid(d)

        def test_value_serializes(self):
            KV3File(value=None).ToString()
            KV3File(value=True).ToString()
            KV3File(value=False).ToString()
            KV3File(value=1).ToString()
            KV3File(value=1.0).ToString()
            KV3File(value=self.MyKV3IntEnum.FIRE).ToString()
            KV3File(value=str()).ToString()
            KV3File(value=str_multiline()).ToString()
            KV3File(value=[]).ToString()
            KV3File(value={}).ToString()
            KV3File(value=bytes(byte for byte in range(256))).ToString()
            KV3File(value=bytearray(byte for byte in range(256))).ToString()

    unittest.main()
