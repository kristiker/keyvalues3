"""
Binary reader code from SourceIO, a Blender plugin for importing Source 2 assets.
https://github.com/REDxEYE/SourceIO

MIT License
Copyright (c) 2020 REDxEYE
"""

import keyvalues3 as kv3
#from binarywriter import BinaryMagics

class KV3TextReader:
    pass


## enums.py

from enum import IntEnum, IntFlag, auto

from SourceIO.library.utils import ExtendedEnum


class BinaryMagics(ExtendedEnum):
    VKV_LEGACY = b'VKV\x03'
    KV3_V1 = b'\x013VK'
    KV3_V2 = b'\x023VK'
    KV3_V3 = b'\x033VK'
    KV3_V4 = b'\x043VK'
    KV3_V5 = b'\x053VK'


class KV3Encodings(ExtendedEnum):
    KV3_ENCODING_BINARY_BLOCK_COMPRESSED = b"\x46\x1A\x79\x95\xBC\x95\x6C\x4F\xA7\x0B\x05\xBC\xA1\xB7\xDF\xD2"
    KV3_ENCODING_BINARY_UNCOMPRESSED = b"\x00\x05\x86\x1B\xD8\xF7\xC1\x40\xAD\x82\x75\xA4\x82\x67\xE7\x14"
    KV3_ENCODING_BINARY_BLOCK_LZ4 = b"\x8A\x34\x47\x68\xA1\x63\x5C\x4F\xA1\x97\x53\x80\x6F\xD9\xB1\x19"


class KV3CompressionMethod(IntEnum, ExtendedEnum):
    UNCOMPRESSED = 0
    LZ4 = 1
    ZSTD = 2


class KV3Formats(ExtendedEnum):
    KV3_FORMAT_GENERIC = b"\x7C\x16\x12\x74\xE9\x06\x98\x46\xAF\xF2\xE6\x3E\xB5\x90\x37\xE7"


class KV3Type(IntEnum):
    NULL = 1
    BOOLEAN = 2
    INT64 = 3
    UINT64 = 4
    DOUBLE = 5
    STRING = 6
    BINARY_BLOB = 7
    ARRAY = 8
    OBJECT = 9
    ARRAY_TYPED = 10
    INT32 = 11
    UINT32 = 12

    BOOLEAN_TRUE = 13
    BOOLEAN_FALSE = 14
    INT64_ZERO = 15
    INT64_ONE = 16
    DOUBLE_ZERO = 17
    DOUBLE_ONE = 18
    FLOAT = 19
    INT16 = 20
    UINT16 = 21
    INT8 = 22
    UINT8 = 23
    ARRAY_TYPED_BYTE_LENGTH = 24
    ARRAY_TYPED_BYTE_LENGTH2 = 25


class Specifier(IntEnum):
    INVALID = 0
    RESOURCE = 1
    RESOURCE_NAME = 2
    PANORAMA = 3
    SOUNDEVENT = 4
    SUBCLASS = 5
    ENTITY_NAME = 6
    LOCALIZE = 7
    UNSPECIFIED = 8
    NULL = 9
    BINARY_BLOB = 10
    ARRAY = 11
    TABLE = 12
    BOOL8 = 13
    CHAR8 = 14
    UCHAR32 = 15
    INT8 = 16
    UINT8 = 17
    INT16 = 18
    UINT16 = 19
    INT32 = 20
    UINT32 = 21
    INT64 = 22
    UINT64 = 23
    FLOAT32 = 24
    FLOAT64 = auto()
    STRING = auto()
    POINTER = auto()
    COLOR32 = auto()
    VECTOR = auto()
    VECTOR2D = auto()
    VECTOR4D = auto()
    ROTATION_VECTOR = auto()
    QUATERNION = auto()
    QANGLE = auto()
    MATRIX3X4 = auto()
    TRANSFORM = auto()
    STRING_TOKEN = auto()
    EHANDLE = auto()


#__all__ = ['KV3Type', 'BinaryMagics', 'KV3Formats', 'KV3Encodings', 'KV3CompressionMethod',
#           'Specifier']

## types.py

import abc
from functools import partial
from types import NoneType
from typing import Collection, Optional, TypeVar

import numpy as np

from .enums import KV3Type, Specifier


class BaseType(abc.ABC):
    def __init_subclass__(cls, **kwargs):
        cls.specifier: Specifier = Specifier.UNSPECIFIED

    def to_dict(self):
        return NotImplemented


class NullObject(BaseType):
    def __bool__(self):
        return False

    def to_dict(self):
        return None


class String(BaseType, str):
    def to_dict(self):
        return str(self)


class _BaseInt(BaseType, int):
    def to_dict(self):
        return int(self)


class _BaseFloat(BaseType, float):
    def to_dict(self):
        return float(self)


class Bool(_BaseInt):
    pass


class Int32(_BaseInt):
    pass


class UInt32(_BaseInt):
    pass


class Int64(_BaseInt):
    pass


class UInt64(_BaseInt):
    pass


class Double(_BaseFloat):
    pass


class Float(_BaseFloat):
    pass


class BinaryBlob(BaseType, bytes):

    def to_dict(self):
        return bytes(self)


T = TypeVar('T', BaseType, str, NoneType)

DEBUGGING = False


class Object(BaseType, dict):
    def __setitem__(self, key, value: T):
        if DEBUGGING:
            if isinstance(value, np.ndarray):
                assert value.dtype in (np.float32, np.float64,
                                       np.int8, np.uint8,
                                       np.int16, np.uint16,
                                       np.int32, np.uint32,
                                       np.int64, np.uint64)
            elif not isinstance(value, (BaseType, str, NoneType)):
                raise TypeError(f'Only KV3 types are allowed, got {type(value)}')
        super(Object, self).__setitem__(key, value)

    def __contains__(self, item):
        if isinstance(item, tuple):
            for key in item:
                if dict.__contains__(self, key):
                    return True
            return False
        else:
            return dict.__contains__(self, item)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            for key in item:
                if dict.__contains__(self, key):
                    return dict.__getitem__(self, key)
            raise KeyError(item)
        else:
            return dict.__getitem__(self, item)

    def to_dict(self):
        if any(isinstance(i, np.ndarray) for i in self.values()):
            res = {}
            for k, v in self.items():
                if v is not None:
                    if isinstance(v, np.ndarray):
                        v = v.tolist()
                    else:
                        v = v.to_dict()
                res[k] = v
            return res
        return {k: v.to_dict() for (k, v) in self.items()}


class Array(BaseType, list[T]):
    def __init__(self, initial: Optional[list[T]] = None):
        super(Array, self).__init__(initial)

    def append(self, value: T):
        assert isinstance(value, BaseType)
        super(Array, self).append(value)

    def extend(self, values: Collection[T]):
        assert all(map(partial(isinstance, __class_or_tuple=BaseType), values))
        super(Array, self).extend(values)

    def to_dict(self):
        if any(isinstance(i, np.ndarray) for i in self):
            res = []
            for i in self:
                if isinstance(i, np.ndarray):
                    i = i.tolist()
                else:
                    i = i.to_dict()
                res.append(i)
            return res
        return [(i.to_dict() if i is not None else None) for i in self]


class TypedArray(BaseType, list[T]):
    def __init__(self, data_type: KV3Type, data_specifier: Specifier, initial: Optional[list[T]] = None):
        super(TypedArray, self).__init__(initial)
        self.data_type = data_type
        self.data_specifier = data_specifier

    def append(self, value: T):
        assert isinstance(value, BaseType)
        super(TypedArray, self).append(value)

    def extend(self, values: Collection[T]):
        assert all(map(partial(isinstance, __class_or_tuple=BaseType), values))
        super(TypedArray, self).extend(values)

    def to_dict(self):
        if any(isinstance(i, np.ndarray) for i in self):
            res = []
            for i in self:
                if isinstance(i, np.ndarray):
                    i = i.tolist()
                else:
                    i = i.to_dict()
                res.append(i)
            return res
        return [i.to_dict() for i in self]


AnyKVType = Object | NullObject | String | Bool | Int64 | Int32 | UInt64 | UInt32 | Double | Float | BinaryBlob | Array | TypedArray

#__all__ = ['BaseType', 'Object', 'NullObject', 'String', 'Bool',
#           'Int64', 'UInt32', 'UInt64', 'Int32', 'Double', 'Float',
#           'BinaryBlob', 'Array', 'TypedArray', 'AnyKVType']


from dataclasses import dataclass
from typing import Any, Optional, Callable

import numpy as np

from SourceIO.library.utils import Buffer, MemoryBuffer, WritableMemoryBuffer
from SourceIO.library.utils.rustlib import LZ4ChainDecoder, lz4_decompress, zstd_decompress_stream, zstd_decompress
from SourceIO.library.utils.perf_sampler import timed
from .enums import *
from .types import *


class UnsupportedVersion(Exception):
    pass


@dataclass(slots=True)
class KV3Context:
    byte_buffer: Buffer
    short_buffer: Buffer | None
    int_buffer: Buffer
    double_buffer: Buffer

    type_buffer: Buffer
    blocks_buffer: Optional[Buffer]
    object_member_counts: Buffer

    read_type: Callable[['KV3Context'], tuple[KV3Type, Specifier, Specifier]]


def _legacy_block_decompress(in_buffer: Buffer) -> Buffer:
    out_buffer = WritableMemoryBuffer()
    flags = in_buffer.read(4)
    if flags[3] & 0x80:
        out_buffer.write(in_buffer.read(-1))
    working = True
    while in_buffer.tell() != in_buffer.size() and working:
        block_mask = in_buffer.read_uint16()
        for i in range(16):
            if block_mask & (1 << i) > 0:
                offset_and_size = in_buffer.read_uint16()
                offset = ((offset_and_size & 0xFFF0) >> 4) + 1
                size = (offset_and_size & 0x000F) + 3
                lookup_size = offset if offset < size else size

                entry = out_buffer.tell()
                out_buffer.seek(entry - offset)
                data = out_buffer.read(lookup_size)
                out_buffer.seek(entry)
                while size > 0:
                    out_buffer.write(data[:lookup_size if lookup_size < size else size])
                    size -= lookup_size
            else:
                data = in_buffer.read_int8()
                out_buffer.write_int8(data)
            if out_buffer.size() == (flags[2] << 16) + (flags[1] << 8) + flags[0]:
                working = False
                break
    out_buffer.seek(0)
    return out_buffer


@timed
def read_valve_keyvalue3(buffer: Buffer) -> AnyKVType:
    sig = buffer.read(4)
    if not BinaryMagics.is_valid(sig):
        raise BufferError("Not a KV3 buffer")
    sig = BinaryMagics(sig)
    encoding = buffer.read(16)
    if sig == BinaryMagics.VKV:
        return read_legacy(encoding, buffer)
    elif sig == BinaryMagics.KV3_V1:
        return read_v1(encoding, buffer)
    elif sig == BinaryMagics.KV3_V2:
        return read_v2(encoding, buffer)
    elif sig == BinaryMagics.KV3_V3:
        return read_v3(encoding, buffer)
    elif sig == BinaryMagics.KV3_V4:
        return read_v4(encoding, buffer)
    elif sig == BinaryMagics.KV3_V5:
        return read_v5(encoding, buffer)
    raise UnsupportedVersion(f"Unsupported KV3 version: {sig!r}")

@dataclass
class KV3Buffers:
    byte_buffer: Buffer
    short_buffer: Buffer | None
    int_buffer: Buffer
    double_buffer: Buffer


@dataclass
class KV3ContextNew:
    strings: list[str]
    buffer0: KV3Buffers
    buffer1: KV3Buffers

    types_buffer: Buffer
    object_member_count_buffer: Buffer
    binary_blob_sizes: list[int] | None
    binary_blob_buffer: Buffer | None

    read_type: Callable[['KV3ContextNew'], tuple[KV3Type, Specifier]]
    read_value: Callable[['KV3ContextNew'], AnyKVType]
    active_buffer: KV3Buffers | None = None


def _read_boolean(context: KV3ContextNew, specifier: Specifier):
    value = Bool(context.active_buffer.byte_buffer.read_uint8() == 1)
    value.specifier = specifier
    return value


def _read_int64(context: KV3ContextNew, specifier: Specifier):
    value = Int64(context.active_buffer.double_buffer.read_int64())
    value.specifier = specifier
    return value


def _read_uint64(context: KV3ContextNew, specifier: Specifier):
    value = UInt64(context.active_buffer.double_buffer.read_uint64())
    value.specifier = specifier
    return value


def _read_double(context: KV3ContextNew, specifier: Specifier):
    value = Double(context.active_buffer.double_buffer.read_double())
    value.specifier = specifier
    return value


def _read_string(context: KV3ContextNew, specifier: Specifier):
    str_id = context.active_buffer.int_buffer.read_int32()
    if str_id == -1:
        value = String('')
    else:
        value = String(context.strings[str_id])
    value.specifier = specifier
    return value


def _read_blob(context: KV3ContextNew, specifier: Specifier):
    if context.binary_blob_sizes is not None:
        expected_size = context.binary_blob_sizes.pop(0)
        if expected_size == 0:
            value = BinaryBlob(b"")
        else:
            data = context.binary_blob_buffer.read(expected_size)
            assert len(data) == expected_size, "Binary blob is smaller than expected"
            value = BinaryBlob(data)
    else:
        value = BinaryBlob(context.active_buffer.byte_buffer.read(context.active_buffer.int_buffer.read_int32()))
    value.specifier = specifier
    return value


def _read_array(context: KV3ContextNew, specifier: Specifier):
    count = context.active_buffer.int_buffer.read_int32()
    array = Array([None] * count)
    for i in range(count):
        array[i] = context.read_value(context)
    return array


def _read_object(context: KV3ContextNew, specifier: Specifier):
    member_count = context.object_member_count_buffer.read_uint32()
    obj = Object()
    for i in range(member_count):
        name_id = context.active_buffer.int_buffer.read_int32()
        name = context.strings[name_id] if name_id != -1 else str(i)
        obj[name] = context.read_value(context)
    obj.specifier = specifier
    return obj


def _read_array_typed_helper(context: KV3ContextNew, count, specifier: Specifier):
    buffers = context.active_buffer
    data_type, data_specifier = context.read_type(context)
    if data_type == KV3Type.DOUBLE_ZERO:
        return np.zeros(count, np.float64)
    elif data_type == KV3Type.DOUBLE_ONE:
        return np.ones(count, np.float64)
    elif data_type == KV3Type.INT64_ZERO:
        return np.zeros(count, np.int64)
    elif data_type == KV3Type.INT64_ONE:
        return np.ones(count, np.int64)
    elif data_type == KV3Type.DOUBLE:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.float64)
    elif data_type == KV3Type.INT64:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.int64)
    elif data_type == KV3Type.UINT64:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.uint64)
    elif data_type == KV3Type.INT32:
        return np.frombuffer(buffers.int_buffer.read(4 * count), np.int32)
    elif data_type == KV3Type.UINT32:
        return np.frombuffer(buffers.int_buffer.read(4 * count), np.uint32)
    else:
        reader = _kv3_readers[data_type]
        return TypedArray(data_type, data_specifier, [reader(context, data_specifier) for _ in range(count)])


def _read_array_typed(context: KV3ContextNew, specifier: Specifier):
    count = context.active_buffer.int_buffer.read_uint32()
    array = _read_array_typed_helper(context, count, specifier)
    if isinstance(array, BaseType):
        array.specifier = specifier
    return array


def _read_array_typed_byte_size(context: KV3ContextNew, specifier: Specifier):
    count = context.active_buffer.byte_buffer.read_uint8()
    array = _read_array_typed_helper(context, count, specifier)
    if isinstance(array, BaseType):
        array.specifier = specifier
    return array


def _read_array_typed_byte_size2(context: KV3ContextNew, specifier: Specifier):
    count = context.active_buffer.byte_buffer.read_uint8()
    assert specifier == Specifier.UNSPECIFIED, f"Unsupported specifier {specifier!r}"
    context.active_buffer = context.buffer0
    array = _read_array_typed_helper(context, count, specifier)
    context.active_buffer = context.buffer1
    if isinstance(array, BaseType):
        array.specifier = specifier
    return array


def _read_int32(context: KV3ContextNew, specifier: Specifier):
    value = Int32(context.active_buffer.int_buffer.read_int32())
    value.specifier = specifier
    return value


def _read_uint32(context: KV3ContextNew, specifier: Specifier):
    value = UInt32(context.active_buffer.int_buffer.read_uint32())
    value.specifier = specifier
    return value


def _read_float(context: KV3ContextNew, specifier: Specifier):
    value = Float(context.active_buffer.int_buffer.read_float())
    value.specifier = specifier
    return value


def _read_int16(context: KV3ContextNew, specifier: Specifier):
    value = Int32(context.active_buffer.short_buffer.read_int16())
    value.specifier = specifier
    return value


def _read_uint16(context: KV3ContextNew, specifier: Specifier):
    value = UInt32(context.active_buffer.short_buffer.read_uint16())
    value.specifier = specifier
    return value


def _read_int8(context: KV3ContextNew, specifier: Specifier):
    value = Int32(context.active_buffer.byte_buffer.read_uint8())
    value.specifier = specifier
    return value


def _read_uint8(context: KV3ContextNew, specifier: Specifier):
    value = UInt32(context.active_buffer.byte_buffer.read_uint8())
    value.specifier = specifier
    return value


_kv3_readers: list[Callable[['KV3ContextNew', Specifier], Any] | None] = [
    None,
    lambda a, c: None,
    _read_boolean,
    _read_int64,
    _read_uint64,
    _read_double,
    _read_string,
    _read_blob,
    _read_array,
    _read_object,
    _read_array_typed,
    _read_int32,
    _read_uint32,
    lambda a, c: Bool(True),
    lambda a, c: Bool(False),
    lambda a, c: Int64(0),
    lambda a, c: Int64(1),
    lambda a, c: Double(0.0),
    lambda a, c: Double(1.0),
    _read_float,
    _read_int16,
    _read_uint16,
    _read_int8,
    _read_uint8,
    _read_array_typed_byte_size,
    _read_array_typed_byte_size2,
]


@timed
def _read_value_legacy(context: KV3ContextNew):
    value_type, specifier = context.read_type(context)
    reader = _kv3_readers[value_type]
    if reader is None:
        raise NotImplementedError(f"Reader for {value_type!r} not implemented")

    return reader(context, specifier)


def _read_type_legacy(context: KV3ContextNew):
    data_type = context.types_buffer.read_uint8()
    specifier = Specifier.UNSPECIFIED

    if data_type & 0x80:
        data_type &= 0x7F
        flag = context.types_buffer.read_uint8()
        if flag & 1:
            specifier = Specifier.RESOURCE
        elif flag & 2:
            specifier = Specifier.RESOURCE_NAME
        elif flag & 8:
            specifier = Specifier.PANORAMA
        elif flag & 16:
            specifier = Specifier.SOUNDEVENT
        elif flag & 32:
            specifier = Specifier.SUBCLASS
    return KV3Type(data_type), specifier


def _read_type_v3(context: KV3ContextNew):
    data_type = context.types_buffer.read_uint8()
    specifier = Specifier.UNSPECIFIED

    if data_type & 0x80:
        data_type &= 0x3F
        flag = context.types_buffer.read_uint8()
        if flag & 1:
            specifier = Specifier.RESOURCE
        elif flag & 2:
            specifier = Specifier.RESOURCE_NAME
        elif flag & 8:
            specifier = Specifier.PANORAMA
        elif flag & 16:
            specifier = Specifier.SOUNDEVENT
        elif flag & 32:
            specifier = Specifier.SUBCLASS
    return KV3Type(data_type), specifier


def split_buffer(data_buffer: Buffer, bytes_count: int, short_count: int, int_count: int, double_count: int,
                 force_align=False):
    bytes_buffer = MemoryBuffer(data_buffer.read(bytes_count))
    if short_count or force_align:
        data_buffer.align(2)
    shorts_buffer = MemoryBuffer(data_buffer.read(short_count * 2))
    if int_count or force_align:
        data_buffer.align(4)
    ints_buffer = MemoryBuffer(data_buffer.read(int_count * 4))
    if double_count or force_align:
        data_buffer.align(8)
    doubles_buffer = MemoryBuffer(data_buffer.read(double_count * 8))

    return KV3Buffers(bytes_buffer, shorts_buffer, ints_buffer, doubles_buffer)


@timed
def read_legacy(encoding: bytes, buffer: Buffer):
    if not KV3Encodings.is_valid(encoding):
        raise BufferError(f'Buffer contains unknown encoding: {encoding!r}')
    encoding = KV3Encodings(encoding)
    fmt = buffer.read(16)

    if encoding == KV3Encodings.KV3_ENCODING_BINARY_UNCOMPRESSED:
        buffer = MemoryBuffer(buffer.read())
    elif encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_COMPRESSED:
        buffer = _legacy_block_decompress(buffer)
    elif encoding == KV3Encodings.KV3_ENCODING_BINARY_BLOCK_LZ4:
        decompressed_size = buffer.read_uint32()
        buffer = MemoryBuffer(lz4_decompress(buffer.read(-1), decompressed_size))
    else:
        raise ValueError("Unsupported Legacy encoding")

    strings = [buffer.read_ascii_string() for _ in range(buffer.read_uint32())]

    buffers = KV3Buffers(buffer, None, buffer, buffer)
    context = KV3ContextNew(
        strings=strings,
        buffer0=buffers,
        buffer1=buffers,
        types_buffer=buffer,
        object_member_count_buffer=buffer,
        binary_blob_sizes=None,
        binary_blob_buffer=None,
        read_type=_read_type_legacy,
        read_value=_read_value_legacy,

        active_buffer=buffers
    )
    root = context.read_value(context)
    return root


@timed
def read_v1(encoding: bytes, buffer: Buffer):
    compression_method = buffer.read_uint32()

    bytes_count = buffer.read_uint32()
    ints_count = buffer.read_uint32()
    doubles_count = buffer.read_uint32()

    uncompressed_size = buffer.read_uint32()

    if compression_method == 0:
        buffer = MemoryBuffer(buffer.read(uncompressed_size))
    elif compression_method == 1:
        u_data = lz4_decompress(buffer.read(-1), uncompressed_size)
        assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
        buffer = MemoryBuffer(u_data)
        del u_data
    else:
        raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

    kv_buffer = split_buffer(buffer, bytes_count, 0, ints_count, doubles_count, force_align=True)

    strings = [buffer.read_ascii_string() for _ in range(kv_buffer.int_buffer.read_uint32())]
    types_buffer = MemoryBuffer(buffer.read(-1))

    context = KV3ContextNew(
        strings=strings,
        buffer0=kv_buffer,
        buffer1=kv_buffer,
        types_buffer=types_buffer,
        object_member_count_buffer=kv_buffer.int_buffer,
        binary_blob_sizes=None,
        binary_blob_buffer=None,
        read_type=_read_type_legacy,
        read_value=_read_value_legacy,

        active_buffer=kv_buffer
    )
    root = context.read_value(context)
    return root


@timed
def read_v2(encoding: bytes, buffer: Buffer):
    compression_method = buffer.read_uint32()
    compression_dict_id = buffer.read_uint16()
    compression_frame_size = buffer.read_uint16()

    bytes_count = buffer.read_uint32()
    ints_count = buffer.read_uint32()
    doubles_count = buffer.read_uint32()

    strings_types_size, object_count, array_count = buffer.read_fmt('I2H')

    uncompressed_size = buffer.read_uint32()
    compressed_size = buffer.read_uint32()
    block_count = buffer.read_uint32()
    block_total_size = buffer.read_uint32()

    if compression_method == 0:
        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        if compression_frame_size != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        data_buffer = MemoryBuffer(buffer.read(compressed_size))
    elif compression_method == 1:

        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        if compression_frame_size != 16384:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        data = buffer.read(compressed_size)
        u_data = lz4_decompress(data, uncompressed_size)
        assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    elif compression_method == 2:
        data = buffer.read(compressed_size)
        u_data = zstd_decompress_stream(data, )
        assert len(
            u_data) == uncompressed_size + block_total_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    else:
        raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

    bytes_buffer = MemoryBuffer(data_buffer.read(bytes_count))
    data_buffer.align(4)
    ints_buffer = MemoryBuffer(data_buffer.read(ints_count * 4))
    data_buffer.align(8)
    doubles_buffer = MemoryBuffer(data_buffer.read(doubles_count * 8))

    types_buffer = MemoryBuffer(data_buffer.read(strings_types_size))

    strings = [types_buffer.read_ascii_string() for _ in range(ints_buffer.read_uint32())]

    if block_count == 0:
        block_sizes = []
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_buffer = None

    else:
        block_sizes = [data_buffer.read_uint32() for _ in range(block_count)]
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_data = b''
        if block_total_size > 0:
            if compression_method == 0:
                for uncompressed_block_size in block_sizes:
                    block_data += data_buffer.read(uncompressed_block_size)
            elif compression_method == 1:
                cd = LZ4ChainDecoder(compression_frame_size, 0)
                for block_size in block_sizes:
                    block_size_tmp = block_size
                    while data_buffer.tell() < data_buffer.size() and block_size_tmp > 0:
                        compressed_block_size = data_buffer.read_uint16()
                        decompressed = cd.decompress(buffer.read(compressed_block_size), compression_frame_size)
                        if len(decompressed) > block_size_tmp:
                            decompressed = decompressed[:block_size_tmp]
                            block_size_tmp = 0
                        elif block_size_tmp < 0:
                            raise ValueError("Failed to decompress blocks!")
                        else:
                            block_size_tmp -= len(decompressed)
                        block_data += decompressed
            elif compression_method == 2:
                block_data += data_buffer.read()
            else:
                raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")
        block_buffer = MemoryBuffer(block_data)

    def _read_type(context: KV3ContextNew):
        data_type = context.types_buffer.read_uint8()
        specifier = Specifier.UNSPECIFIED

        if data_type & 0x80:
            data_type &= 0x7F
            flag = context.types_buffer.read_uint8()
            if flag & 1:
                specifier = Specifier.RESOURCE
            elif flag & 2:
                specifier = Specifier.RESOURCE_NAME
            elif flag & 8:
                specifier = Specifier.PANORAMA
            elif flag & 16:
                specifier = Specifier.SOUNDEVENT
            elif flag & 32:
                specifier = Specifier.SUBCLASS
        return KV3Type(data_type), specifier

    buffers = KV3Buffers(bytes_buffer, None, ints_buffer, doubles_buffer)
    context = KV3ContextNew(
        strings=strings,
        buffer0=buffers,
        buffer1=buffers,
        types_buffer=types_buffer,
        object_member_count_buffer=ints_buffer,
        binary_blob_sizes=block_sizes,
        binary_blob_buffer=block_buffer,
        read_type=_read_type,
        read_value=_read_value_legacy,
        active_buffer=buffers
    )
    root = context.read_value(context)
    return root


@timed
def read_v3(encoding: bytes, buffer: Buffer):
    compression_method = buffer.read_uint32()
    compression_dict_id = buffer.read_uint16()
    compression_frame_size = buffer.read_uint16()

    bytes_count = buffer.read_uint32()
    ints_count = buffer.read_uint32()
    doubles_count = buffer.read_uint32()

    strings_types_size, object_count, array_count = buffer.read_fmt('I2H')

    uncompressed_size = buffer.read_uint32()
    compressed_size = buffer.read_uint32()
    block_count = buffer.read_uint32()
    block_total_size = buffer.read_uint32()

    if compression_method == 0:
        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        if compression_frame_size != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        data_buffer = MemoryBuffer(buffer.read(compressed_size))
    elif compression_method == 1:

        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        if compression_frame_size != 16384:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        data = buffer.read(compressed_size)
        u_data = lz4_decompress(data, uncompressed_size)
        assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    elif compression_method == 2:
        data = buffer.read(compressed_size)
        u_data = zstd_decompress_stream(data)
        assert len(
            u_data) == uncompressed_size + block_total_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    else:
        raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

    kv_buffer = split_buffer(data_buffer, bytes_count, 0, ints_count, doubles_count, True)

    types_buffer = MemoryBuffer(data_buffer.read(strings_types_size))

    strings = [types_buffer.read_ascii_string() for _ in range(kv_buffer.int_buffer.read_uint32())]

    if block_count == 0:
        block_sizes = []
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_buffer = None

    else:
        block_sizes = [data_buffer.read_uint32() for _ in range(block_count)]
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_data = b''
        if block_total_size > 0:
            if compression_method == 0:
                for uncompressed_block_size in block_sizes:
                    block_data += data_buffer.read(uncompressed_block_size)
            elif compression_method == 1:
                compressed_sizes = [data_buffer.read_uint16() for _ in range(data_buffer.remaining() // 2)]
                block_data = decompress_lz4_chain(buffer, block_sizes, compressed_sizes, compression_frame_size)
            elif compression_method == 2:
                block_data += data_buffer.read()
            else:
                raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")
        block_buffer = MemoryBuffer(block_data)

    context = KV3ContextNew(
        strings=strings,
        buffer0=kv_buffer,
        buffer1=kv_buffer,
        types_buffer=types_buffer,
        object_member_count_buffer=kv_buffer.int_buffer,
        binary_blob_sizes=block_sizes,
        binary_blob_buffer=block_buffer,
        read_type=_read_type_v3,
        read_value=_read_value_legacy,
        active_buffer=kv_buffer
    )
    root = context.read_value(context)
    return root


@timed
def read_v4(encoding: bytes, buffer: Buffer):
    compression_method = buffer.read_uint32()
    compression_dict_id = buffer.read_uint16()
    compression_frame_size = buffer.read_uint16()

    bytes_count = buffer.read_uint32()
    ints_count = buffer.read_uint32()
    doubles_count = buffer.read_uint32()

    strings_types_size, object_count, array_count = buffer.read_fmt('I2H')

    uncompressed_size = buffer.read_uint32()
    compressed_size = buffer.read_uint32()
    block_count = buffer.read_uint32()
    block_total_size = buffer.read_uint32()

    short_count = buffer.read_uint32()
    compressed_block_sizes = buffer.read_uint32() // 2
    # if block_count>0:
    #     assert compressed_block_sizes>0

    if compression_method == 0:
        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        if compression_frame_size != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        data_buffer = MemoryBuffer(buffer.read(compressed_size))
    elif compression_method == 1:

        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        if compression_frame_size != 16384:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        data = buffer.read(compressed_size)
        u_data = lz4_decompress(data, uncompressed_size)
        assert len(u_data) == uncompressed_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    elif compression_method == 2:
        data = buffer.read(compressed_size)
        u_data = zstd_decompress_stream(data, )
        assert len(
            u_data) == uncompressed_size + block_total_size, "Decompressed data size does not match expected size"
        data_buffer = MemoryBuffer(u_data)
        del u_data, data
    else:
        raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

    kv_buffer = split_buffer(data_buffer, bytes_count, short_count, ints_count, doubles_count, True)

    types_buffer = MemoryBuffer(data_buffer.read(strings_types_size))

    strings = [types_buffer.read_ascii_string() for _ in range(kv_buffer.int_buffer.read_uint32())]

    if block_count == 0:
        block_sizes = []
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_buffer = None

    else:
        block_sizes = [data_buffer.read_uint32() for _ in range(block_count)]
        assert data_buffer.read_uint32() == 0xFFEEDD00
        block_data = b''
        if block_total_size > 0:
            if compression_method == 0:
                for uncompressed_block_size in block_sizes:
                    block_data += data_buffer.read(uncompressed_block_size)
            elif compression_method == 1:
                compressed_sizes = [data_buffer.read_uint16() for _ in range(data_buffer.remaining() // 2)]
                block_data = decompress_lz4_chain(buffer, block_sizes, compressed_sizes, compression_frame_size)
            elif compression_method == 2:
                block_data += data_buffer.read()
            else:
                raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")
        block_buffer = MemoryBuffer(block_data)

    context = KV3ContextNew(
        strings=strings,
        buffer0=kv_buffer,
        buffer1=kv_buffer,
        types_buffer=types_buffer,
        object_member_count_buffer=kv_buffer.int_buffer,
        binary_blob_sizes=block_sizes,
        binary_blob_buffer=block_buffer,
        read_type=_read_type_v3,
        read_value=_read_value_legacy,
        active_buffer=kv_buffer
    )
    root = context.read_value(context)
    return root


@timed
def read_v5(encoding: bytes, buffer: Buffer):
    compression_method = buffer.read_uint32()
    compression_dict_id = buffer.read_uint16()
    compression_frame_size = buffer.read_uint16()

    bytes_count = buffer.read_uint32()
    int_count = buffer.read_uint32()
    double_count = buffer.read_uint32()

    types_size, object_count, array_count = buffer.read_fmt('I2H')

    uncompressed_total_size = buffer.read_uint32()
    compressed_total_size = buffer.read_uint32()
    block_count = buffer.read_uint32()
    block_total_size = buffer.read_uint32()
    short_count = buffer.read_uint32()
    compressed_block_sizes = buffer.read_uint32() // 2
    # assert unk == 0

    buffer0_decompressed_size, block0_compressed_size = buffer.read_fmt("2I")
    buffer1_decompressed_size, block1_compressed_size = buffer.read_fmt("2I")
    bytes_count2, short_count2, int_count2, double_count2 = buffer.read_fmt("4I")
    (field_54, object_count_v5, field_5c, field_60) = buffer.read_fmt("4I")

    if compression_method > 0:
        compressed_buffer0 = buffer.read(block0_compressed_size)
        compressed_buffer1 = buffer.read(block1_compressed_size)
    else:
        compressed_buffer0 = buffer.read(buffer0_decompressed_size)
        compressed_buffer1 = buffer.read(buffer1_decompressed_size)

    if compression_method == 0:
        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        if compression_frame_size != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')
        buffer0 = MemoryBuffer(compressed_buffer0)
        buffer1 = MemoryBuffer(compressed_buffer1)
    elif compression_method == 1:

        if compression_dict_id != 0:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        if compression_frame_size != 16384:
            raise NotImplementedError('Unknown compression method in KV3 v2 block')

        u_data = lz4_decompress_wrp(compressed_buffer0, buffer0_decompressed_size)
        assert len(u_data) == buffer0_decompressed_size, "Decompressed data size does not match expected size"
        buffer0 = MemoryBuffer(u_data)
        u_data = lz4_decompress_wrp(compressed_buffer1, buffer1_decompressed_size)
        assert len(u_data) == buffer1_decompressed_size, "Decompressed data size does not match expected size"
        buffer1 = MemoryBuffer(u_data)
    elif compression_method == 2:
        u_data = zstd_decompress_stream_wrp(compressed_buffer0)
        assert len(u_data) == buffer0_decompressed_size, "Decompressed data size does not match expected size"
        buffer0 = MemoryBuffer(u_data)
        u_data = zstd_decompress_stream_wrp(compressed_buffer1)
        assert len(u_data) == buffer1_decompressed_size, "Decompressed data size does not match expected size"
        buffer1 = MemoryBuffer(u_data)
    else:
        raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")

    del compressed_buffer0, compressed_buffer1

    kv_buffer0 = split_buffer(buffer0, bytes_count, short_count, int_count, double_count)
    strings = [kv_buffer0.byte_buffer.read_ascii_string() for _ in range(kv_buffer0.int_buffer.read_uint32())]
    object_member_count_buffer = MemoryBuffer(buffer1.read(object_count_v5 * 4))
    kv_buffer1 = split_buffer(buffer1, bytes_count2, short_count2, int_count2, double_count2)

    types_buffer = MemoryBuffer(buffer1.read(types_size))

    if block_count == 0:
        block_sizes = None
        blocks_buffer = None
        assert buffer1.read_uint32() == 0xFFEEDD00
    else:
        block_sizes = [buffer1.read_uint32() for _ in range(block_count)]
        assert buffer1.read_uint32() == 0xFFEEDD00
        compressed_sizes = [buffer1.read_uint16() for _ in range(compressed_block_sizes)]
        block_data = b''
        if block_total_size > 0:
            if compression_method == 0:
                for uncompressed_block_size in block_sizes:
                    block_data += buffer.read(uncompressed_block_size)
            elif compression_method == 1:
                block_data = decompress_lz4_chain(buffer, block_sizes, compressed_sizes, compression_frame_size)
            elif compression_method == 2:
                zstd_compressed_data = buffer.read(
                    compressed_total_size - block0_compressed_size - block1_compressed_size)
                block_data = zstd_decompress(zstd_compressed_data, block_total_size)
            else:
                raise NotImplementedError(f"Unknown {compression_method} KV3 compression method")
            assert buffer.read_uint32() == 0xFFEEDD00
        blocks_buffer = MemoryBuffer(block_data)

    @timed
    def _read_type(context: KV3ContextNew):
        t = context.types_buffer.read_int8()
        mask = 63
        if t >= 0:
            specific_type = Specifier.UNSPECIFIED
            pass
        else:
            specific_type = Specifier(context.types_buffer.read_uint8())
        if t & 0x40 != 0:
            raise NotImplementedError(f"t & 0x40 != 0: {t & 0x40}")
            # f = KV3TypeFlag(context.types_buffer.read_uint8())
        return KV3Type(t & mask), specific_type

    context = KV3ContextNew(
        strings=strings,
        buffer0=kv_buffer0,
        buffer1=kv_buffer1,
        types_buffer=types_buffer,
        object_member_count_buffer=object_member_count_buffer,
        binary_blob_sizes=block_sizes,
        binary_blob_buffer=blocks_buffer,
        read_type=_read_type,
        read_value=_read_value_legacy,
        active_buffer=kv_buffer1
    )
    root = context.read_value(context)
    return root


@timed
def zstd_decompress_stream_wrp(data):
    return zstd_decompress_stream(data)


@timed
def lz4_decompress_wrp(data, decomp_size):
    return lz4_decompress(data, decomp_size)


@timed
def decompress_lz4_chain(buffer: Buffer, decompressed_block_sizes: list[int], compressed_block_sizes: list[int],
                         compression_frame_size: int):
    block_data = b""
    cd = LZ4ChainDecoder(compression_frame_size, 0)
    for block_size in decompressed_block_sizes:
        block_size_tmp = block_size
        while buffer.tell() < buffer.size() and block_size_tmp > 0:
            compressed_size = compressed_block_sizes.pop(0)
            block = buffer.read(compressed_size)
            decompressed = cd.decompress(block, compression_frame_size)
            actual_size = min(compression_frame_size, block_size_tmp)
            block_size_tmp -= actual_size
            block_data += decompressed[:actual_size]
    return block_data
