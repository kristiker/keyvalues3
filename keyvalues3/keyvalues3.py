import array
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
            raise ValueError(f"{self!r}: version is not an UUID object")
    def __str__(self):
        return "%s:%s:version{%s}" % (self.__class__.__name__.lower(), self.name, str(self.version))

@dataclasses.dataclass(frozen=True)
class Encoding(_HeaderPiece): pass
@dataclasses.dataclass(frozen=True)
class Format(_HeaderPiece): pass


KV3_ENCODING_BINARY_UNCOMPRESSED = Encoding("binary", UUID("1b860500-f7d8-40c1-ad82-75a48267e714"))
KV3_ENCODING_BINARY_BLOCK_COMPRESSED = Encoding("binarybc", UUID("95791a46-95bc-4f6c-a70b-05bca1b7dfd2"))
KV3_ENCODING_BINARY_BLOCK_LZ4 = Format("binarylz4", UUID("6847348a-63a1-4f5c-a197-53806fd9b119"))
KV3_ENCODING_TEXT = Encoding("text", UUID("e21c7f3c-8a33-41c5-9977-a76d3a32aa0d"))

KV3_FORMAT_GENERIC = Format("generic", UUID("7412167c-06e9-4698-aff2-e63eb59037e7"))

@dataclasses.dataclass(frozen=True)
class KV3Header:
    encoding: Encoding = KV3_ENCODING_TEXT
    format: Format = KV3_FORMAT_GENERIC
    def __str__(self):
        return f"<!-- kv3 {self.encoding} {self.format} -->"


simple_types = None | bool | int | float | enum.IntEnum | str
container_types = list[simple_types] | array.array | dict[str, simple_types]
bytearrays = bytes | bytearray
kv3_types = simple_types | container_types | bytearrays

def check_valid(value: kv3_types):
    match value:
        case flagged_value(actual_value, _):
            return check_valid(actual_value)
        case None | bool() | float() | enum.IntEnum() | str():
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
        case array.array() | bytes() | bytearray():
            pass
        case _:
            raise TypeError(f"Invalid type {type(value)} for KV3 value.")

def is_valid(value: kv3_types) -> bool:
    try:
        check_valid(value)
        return True
    except (ValueError, OverflowError, TypeError):
        return False

@enum.global_enum
class Flag(enum.IntFlag):
    resource = enum.auto()
    resource_name = enum.auto()
    multilinestring = enum.auto()
    panorama = enum.auto()
    soundevent = enum.auto()
    subclass = enum.auto()
    def __str__(self):
        return "|".join(flag.name for flag in self.__class__ if self.value & flag)
    def __call__(self, value: kv3_types):
        return flagged_value(value, self)

@dataclasses.dataclass(slots=True)
class flagged_value:
    value: kv3_types
    flags: Flag = Flag(0)

    def __eq__(self, other):
        if isinstance(other, flagged_value):
            return self.value == other.value and self.flags == other.flags
        else:
            if self.flags == Flag(0) or self.flags == Flag.multilinestring:
                return self.value == other
            return False

kv3_types = kv3_types | flagged_value

@runtime_checkable
class Dataclass(Protocol):
    __dataclass_fields__: dict[str, dataclasses.Field]

class KV3File:
    def __init__(self,
            value: kv3_types | Dataclass = None,
            format: Format = KV3_FORMAT_GENERIC,
            validate_value: bool = False,
            serialize_enums_as_ints: bool = False,
            ):

        self.format = format

        if isinstance(value, Dataclass) and not isinstance(value, flagged_value):
            self.value: dict = dataclasses.asdict(value)
        else:
            self.value: kv3_types = value

        if validate_value:
            check_valid(self.value)

        self.serialize_enums_as_ints = serialize_enums_as_ints

    def __str__(self):
        kv3 = str(KV3Header(encoding=KV3_ENCODING_TEXT, format=self.format)) + "\n"
        def object_serialize(object: kv3_types, indentation_level = 0, dictionary_object = False) -> str:
            indent = ("\t" * (indentation_level))
            indent_nested = ("\t" * (indentation_level + 1))
            match object:
                case flagged_value(value, flags):
                    if flags & Flag.multilinestring:
                        return  f'"""\n{value}"""'
                    if flags:
                        return f"{flags}:{object_serialize(value)}"
                    return object_serialize(value)
                case None:
                    return "null"
                case False:
                    return "false"
                case True:
                    return "true"
                case int():
                    return str(object)
                case float():
                    return str(round(object, 6))
                case enum.IntEnum():
                    if self.serialize_enums_as_ints:
                        return str(object.value)
                    return object.name
                case str():
                    return '"' + object + '"'
                case list():
                    qualifies_for_sameline = len(object) <= 4 and all(isinstance(item, (dict)) == False for item in object)
                    if qualifies_for_sameline:
                        return "[" + ", ".join(object_serialize(item) for item in object) + "]"
                    s = f"\n{indent}[\n"
                    for item in object:
                        s += indent_nested + (object_serialize(item, indentation_level+1) + ",\n")
                    return s + indent + "]"
                case dict():
                    s = indent + "{\n"
                    if dictionary_object:
                        s = "\n" + s
                    for key, value in object.items():
                        s += indent_nested + f"{key} = {object_serialize(value, indentation_level+1, dictionary_object=True)}\n"
                    return s + indent + "}"
                case array.array():
                    return "[ ]" # TODO
                case bytes() | bytearray():
                    return f"#[{' '.join(f'{b:02x}' for b in object)}]"
                case _:
                    raise TypeError(f"Invalid type {type(object)} for KV3 value.")

        kv3 += object_serialize(self.value)

        return kv3

    def ToString(self): return self.__str__()

    #def __bytes__(self):
    #    return bytes(BinaryV1UncompressedWriter(self))

    def ToBytes(self): return self.__bytes__()

    #@classmethod
    #def from_string(cls, string: str):
    #    return KV3TextReader().parse(string)
