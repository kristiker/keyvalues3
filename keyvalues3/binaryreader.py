"""
Binary reader code from SourceIO, a Blender plugin for importing Source 2 assets.
https://github.com/REDxEYE/SourceIO

MIT License
Copyright (c) 2020 REDxEYE
"""

import binascii
from struct import pack, unpack, unpack_from, calcsize
import keyvalues3 as kv3
from keyvalues3.binarywriter import BinaryMagics, BinaryType

class KV3TextReader:
    pass

## enums.py

from enum import IntEnum, auto

class Specifier(IntEnum):
    NONE = 0
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


from dataclasses import dataclass
from typing import Any, Optional, Callable, Type, TypeVar, Union, Protocol
import abc, io, contextlib

import numpy as np

T = TypeVar("T")

class Readable(Protocol):
    @classmethod
    def from_buffer(cls: Type[T], buffer: 'Buffer') -> T:
        ...
 
class Buffer(abc.ABC, io.RawIOBase):
    def __init__(self):
        io.RawIOBase.__init__(self)
        self._endian = '<'

    @contextlib.contextmanager
    def save_current_offset(self):
        entry = self.tell()
        yield
        self.seek(entry)

    @contextlib.contextmanager
    def read_from_offset(self, offset: int):
        entry = self.tell()
        self.seek(offset)
        yield
        self.seek(entry)

    def read_source1_string(self, entry):
        offset = self.read_int32()
        if offset:
            with self.read_from_offset(entry + offset):
                return self.read_nt_string()
        else:
            return ""

    def read_source2_string(self):
        with self.read_from_offset(self.tell() + self.read_int32()):
            return self.read_nt_string()

    @property
    @abc.abstractmethod
    def data(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def size(self):
        raise NotImplementedError()

    def remaining(self):
        return self.size() - self.tell()

    @property
    def preview(self):
        with self.save_current_offset():
            return binascii.hexlify(self.read(64), sep=' ', bytes_per_sep=4).decode('ascii').upper()

    def align(self, align_to):
        value = self.tell()
        padding = (align_to - value % align_to) % align_to
        if padding + self.tell() > self.size():
            return
        self.seek(padding, io.SEEK_CUR)

    def skip(self, size):
        self.seek(size, io.SEEK_CUR)

    def read_fmt(self, fmt):
        return unpack(self._endian + fmt, self.read(calcsize(self._endian + fmt)))

    def _read(self, fmt):
        return unpack(self._endian + fmt, self.read(calcsize(self._endian + fmt)))[0]

    def read_relative_offset32(self):
        return self.tell() + self.read_uint32()

    def read_uint64(self):
        return unpack(self._endian + "Q", self.read(8))[0]

    def read_int64(self):
        return unpack(self._endian + "q", self.read(8))[0]

    def read_uint32(self):
        return unpack(self._endian + "I", self.read(4))[0]

    def read_int32(self):
        return unpack(self._endian + "i", self.read(4))[0]

    def read_uint16(self):
        return unpack(self._endian + "H", self.read(2))[0]

    def read_int16(self):
        return unpack(self._endian + "h", self.read(2))[0]

    def read_uint8(self):
        return unpack(self._endian + "B", self.read(1))[0]

    def read_int8(self):
        return unpack(self._endian + "b", self.read(1))[0]

    def read_float(self):
        return unpack(self._endian + "f", self.read(4))[0]

    def read_double(self):
        return unpack(self._endian + "d", self.read(8))[0]

    def read_nt_string(self):
        buffer = bytearray()

        while True:
            chunk = self.read(min(32, self.remaining()))
            if chunk:
                chunk_end = chunk.find(b'\x00')
            else:
                chunk_end = 0
            if chunk_end >= 0:
                buffer += chunk[:chunk_end]
            else:
                buffer += chunk
            if chunk_end >= 0:
                self.seek(-(len(chunk) - chunk_end - 1), io.SEEK_CUR)
                return buffer.decode('latin', errors='replace')

    def read_ascii_string(self, length: Optional[int] = None):
        if length is not None:
            buffer = self.read(length).strip(b'\x00').rstrip(b'\x00')
            if b'\x00' in buffer:
                buffer = buffer[:buffer.index(b'\x00')]
            return buffer.decode('latin', errors='replace')

        return self.read_nt_string()

    def read_fourcc(self):
        return self.read_ascii_string(4)

    def write_fmt(self, fmt: str, *values):
        self.write(pack(self._endian + fmt, *values))

    def write_uint64(self, value):
        self.write_fmt('Q', value)

    def write_int64(self, value):
        self.write_fmt('q', value)

    def write_uint32(self, value):
        self.write_fmt('I', value)

    def write_int32(self, value):
        self.write_fmt('i', value)

    def write_uint16(self, value):
        self.write_fmt('H', value)

    def write_int16(self, value):
        self.write_fmt('h', value)

    def write_uint8(self, value):
        self.write_fmt('B', value)

    def write_int8(self, value):
        self.write_fmt('b', value)

    def write_float(self, value):
        self.write_fmt('f', value)

    def write_double(self, value):
        self.write_fmt('d', value)

    def write_ascii_string(self, string, zero_terminated=False, length=-1):
        pos = self.tell()
        for c in string:
            self.write(c.encode('ascii'))
        if zero_terminated:
            self.write(b'\x00')
        elif length != -1:
            to_fill = length - (self.tell() - pos)
            if to_fill > 0:
                for _ in range(to_fill):
                    self.write_uint8(0)

    def write_fourcc(self, fourcc):
        self.write_ascii_string(fourcc)

    def peek_uint32(self):
        with self.save_current_offset():
            return self.read_uint32()

    def peek_fmt(self, fmt):
        with self.save_current_offset():
            return self.read_fmt(fmt)

    def peek(self, size: int):
        with self.save_current_offset():
            return self.read(size)

    def set_big_endian(self):
        self._endian = '>'

    def set_little_endian(self):
        self._endian = '<'

    def __bool__(self):
        return self.tell() < self.size()

    def slice(self, offset: Optional[int] = None, size: int = -1) -> 'Buffer':
        raise NotImplementedError

    def read_structure_array(self, offset, count, data_class: Readable):
        if count == 0:
            return []
        self.seek(offset)
        object_list = []
        for _ in range(count):
            obj = data_class.from_buffer(self)
            object_list.append(obj)
        return object_list

    def read_half(self):
        return self.read_fmt("h")[0]


class MemoryBuffer(Buffer):

    def __init__(self, buffer: bytes | bytearray | memoryview):
        super().__init__()
        self._buffer: memoryview = memoryview(buffer)
        self._offset = 0

    @property
    def data(self) -> memoryview:
        return self._buffer

    def size(self):
        return len(self._buffer)

    def _read(self, fmt: str):
        data = unpack_from(self._endian + fmt, self._buffer, self._offset)
        self._offset += calcsize(self._endian + fmt)
        return data[0]

    def read_fmt(self, fmt):
        data = unpack_from(self._endian + fmt, self._buffer, self._offset)
        self._offset += calcsize(self._endian + fmt)
        return data

    def write(self, _b: Union[bytes, bytearray]) -> Optional[int]:
        if self._offset + len(_b) > self.size():
            raise BufferError(f"Not enough space left({self.remaining()}) in buffer to write {len(_b)} bytes")
        self._buffer[self._offset:self._offset + len(_b)] = _b
        self._offset += len(_b)
        return len(_b)

    def read(self, _size: int = -1) -> Optional[bytes]:
        if _size == -1:
            data = self._buffer[self._offset:]
            self._offset += len(data)
            return data.tobytes()
        data = self._buffer[self._offset:self._offset + _size]
        self._offset += _size
        return data.tobytes()

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            self._offset = offset
        elif whence == io.SEEK_CUR:
            self._offset += offset
        elif whence == io.SEEK_END:
            self._offset = self.size() - offset
        else:
            raise ValueError("Invalid whence argument")

        if self._offset > self.size():
            raise BufferError('Offset is out of bounds')

        return self._offset

    def __str__(self) -> str:
        return f'<MemoryBuffer {self.tell()}/{self.size()}>'

    def tell(self) -> int:
        return self._offset

    @property
    def closed(self) -> bool:
        return self._buffer is None

    def close(self) -> None:
        self._buffer = None

    def read_nt_string(self: 'MemoryBuffer'):
        end = self._buffer.obj.index(b"\x00", self._offset)
        string = self._buffer[self._offset:end]
        self._offset+=end-self._offset+1
        return string.tobytes().decode("utf8")

    def slice(self, offset: Optional[int] = None, size: int = -1) -> 'MemorySlice':
        if offset is None:
            offset = self._offset
        slice_offset = self.tell()
        if size == -1:
            return MemorySlice(self._buffer[offset:], slice_offset)
        return MemorySlice(self._buffer[offset:offset + size], slice_offset)

class WritableMemoryBuffer(io.BytesIO, Buffer):
    def __init__(self, initial_bytes=None):
        io.BytesIO.__init__(self, initial_bytes)
        Buffer.__init__(self)

    @property
    def data(self):
        return self.getbuffer()

    def size(self):
        return len(self.getbuffer())

    def slice(self, offset: Optional[int] = None, size: int = -1) -> 'MemorySlice':
        if offset is None:
            offset = self.tell()

        if size == -1:
            return MemoryBuffer(self.data[offset:])
        return MemoryBuffer(self.data[offset:offset + size])
    
class MemorySlice(MemoryBuffer):
    def __init__(self, buffer: Union[bytes, bytearray, memoryview], offset: int):
        super().__init__(buffer)
        self._slice_offset = offset

    def abs_tell(self):
        return self.tell() + self._slice_offset



import lz4.block
import zstandard as zstd

# Replacement functions for the commented SourceIO dependencies
def lz4_decompress(data: bytes, uncompressed_size: int) -> bytes:
    """LZ4 decompression using the lz4 library"""
    return lz4.block.decompress(data, uncompressed_size)

def zstd_decompress_stream(data: bytes) -> bytes:
    """ZSTD decompression using zstandard library"""
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data)

def zstd_decompress(data: bytes, uncompressed_size: int) -> bytes:
    """ZSTD decompression with expected size"""
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data, max_output_size=uncompressed_size)

class LZ4ChainDecoder:
    """Simple LZ4 chain decoder replacement"""
    def __init__(self, frame_size: int, flags: int):
        self.frame_size = frame_size
        self.flags = flags
        self.context = b""
    
    def decompress(self, data: bytes, expected_size: int) -> bytes:
        """Decompress LZ4 data with context"""
        try:
            # For LZ4 chain decompression, we need to maintain context
            # This is a simplified implementation
            decompressed = lz4.block.decompress(data, expected_size, dict=self.context)
            # Update context for next decompression
            if len(decompressed) > self.frame_size:
                self.context = decompressed[-self.frame_size:]
            else:
                self.context = decompressed
            return decompressed
        except Exception:
            # Fallback to regular decompression if chain fails
            return lz4.block.decompress(data, expected_size)


@dataclass(slots=True)
class KV3Context:
    byte_buffer: Buffer
    short_buffer: Buffer | None
    int_buffer: Buffer
    double_buffer: Buffer

    type_buffer: Buffer
    blocks_buffer: Optional[Buffer]
    object_member_counts: Buffer

    read_type: Callable[['KV3Context'], tuple[BinaryType, Specifier, Specifier]]


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


def read_valve_keyvalue3(buffer: Buffer) -> kv3.ValueType:
    magic = buffer.read(4)
    if not BinaryMagics.is_defined(magic):
        raise BufferError("Not a KV3 buffer")
    magic = BinaryMagics(magic)
    if magic == BinaryMagics.VKV3:
        return read_legacy(buffer)
    elif magic == BinaryMagics.KV3_01:
        return read_v1(buffer)
    elif magic == BinaryMagics.KV3_02:
        return read_v2(buffer)
    elif magic == BinaryMagics.KV3_03:
        return read_v3(buffer)
    elif magic == BinaryMagics.KV3_04:
        return read_v4(buffer)
    elif magic == BinaryMagics.KV3_05:
        return read_v5(buffer)
    raise Exception(f"Unsupported KV3 version: {magic!r}")

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

    read_type: Callable[['KV3ContextNew'], tuple[BinaryType, Specifier]]
    read_value: Callable[['KV3ContextNew'], kv3.ValueType]
    active_buffer: KV3Buffers


def _read_int64(context: KV3ContextNew):
    value = context.active_buffer.double_buffer.read_int64()
    return value


def _read_uint64(context: KV3ContextNew):
    value = context.active_buffer.double_buffer.read_uint64()
    return value


def _read_double(context: KV3ContextNew):
    value = context.active_buffer.double_buffer.read_double()
    return value


def _read_string(context: KV3ContextNew):
    str_id = context.active_buffer.int_buffer.read_int32()
    if str_id == -1:
        value = ''
    else:
        value = context.strings[str_id]
    return value


def _read_blob(context: KV3ContextNew):
    if context.binary_blob_sizes is not None:
        expected_size = context.binary_blob_sizes.pop(0)
        if expected_size == 0:
            value = b""
        else:
            data = context.binary_blob_buffer.read(expected_size)
            assert len(data) == expected_size, "Binary blob is smaller than expected"
            value = data
    else:
        value = context.active_buffer.byte_buffer.read(context.active_buffer.int_buffer.read_int32())
    return value


def _read_array(context: KV3ContextNew):
    count = context.active_buffer.int_buffer.read_int32()
    array = [None] * count
    for i in range(count):
        array[i] = context.read_value(context)
    return array


def _read_object(context: KV3ContextNew):
    member_count = context.object_member_count_buffer.read_uint32()
    obj = {}
    for i in range(member_count):
        name_id = context.active_buffer.int_buffer.read_int32()
        name = context.strings[name_id] if name_id != -1 else str(i)
        obj[name] = context.read_value(context)
    return obj


def _read_array_typed_helper(context: KV3ContextNew, count):
    buffers = context.active_buffer
    data_type, data_specifier = context.read_type(context)

    return b"";

    if data_type == BinaryType.double_zero:
        return np.zeros(count, np.float64)
    elif data_type == BinaryType.double_one:
        return np.ones(count, np.float64)
    elif data_type == BinaryType.int64_zero:
        return np.zeros(count, np.int64)
    elif data_type == BinaryType.int64_one:
        return np.ones(count, np.int64)
    elif data_type == BinaryType.double:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.float64)
    elif data_type == BinaryType.int64:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.int64)
    elif data_type == BinaryType.uint64:
        return np.frombuffer(buffers.double_buffer.read(8 * count), np.uint64)
    elif data_type == BinaryType.int32:
        return np.frombuffer(buffers.int_buffer.read(4 * count), np.int32)
    elif data_type == BinaryType.uint32:
        return np.frombuffer(buffers.int_buffer.read(4 * count), np.uint32)
    else:
        reader = _kv3_readers[data_type]
        return TypedArray(data_type, data_specifier, [reader(context, data_specifier) for _ in range(count)])

def _read_array_typed(context: KV3ContextNew):
    count = context.active_buffer.int_buffer.read_uint32()
    array = _read_array_typed_helper(context, count)
    return array


def _read_array_typed_byte_size(context: KV3ContextNew):
    count = context.active_buffer.byte_buffer.read_uint8()
    array = _read_array_typed_helper(context, count)
    return array


def _read_array_typed_byte_size2(context: KV3ContextNew):
    count = context.active_buffer.byte_buffer.read_uint8()
    #assert specifier == Specifier.UNSPECIFIED, f"Unsupported specifier {specifier!r}"
    context.active_buffer = context.buffer0
    array = _read_array_typed_helper(context, count)
    context.active_buffer = context.buffer1
    return array


def _read_int32(context: KV3ContextNew): return context.active_buffer.int_buffer.read_int32()
def _read_uint32(context: KV3ContextNew): return context.active_buffer.int_buffer.read_uint32()


def _read_float(context: KV3ContextNew):
    value = context.active_buffer.int_buffer.read_float()
    return value


def _read_int16(context: KV3ContextNew):
    value = context.active_buffer.short_buffer.read_int16()
    return value


def _read_uint16(context: KV3ContextNew):
    value = context.active_buffer.short_buffer.read_uint16()
    return value


def _read_int8(context: KV3ContextNew):
    value = context.active_buffer.byte_buffer.read_uint8()
    return value


def _read_uint8(context: KV3ContextNew):
    value = context.active_buffer.byte_buffer.read_uint8()
    return value


_kv3_readers: dict[BinaryType, Callable[[KV3ContextNew], kv3.ValueType] | None] = {
    BinaryType.null : lambda _: None,
    BinaryType.boolean : lambda c: _read_uint8(c) == 1,
    BinaryType.int64 : _read_int64,
    BinaryType.uint64 : _read_uint64,
    BinaryType.double : _read_double,
    BinaryType.string : _read_string,
    BinaryType.binary_blob : _read_blob,
    BinaryType.array : _read_array,
    BinaryType.dictionary : _read_object,
    BinaryType.array_typed : _read_array_typed,
    BinaryType.int32 : _read_int32,
    BinaryType.uint32 : _read_uint32,
    BinaryType.boolean_true : lambda _: True,
    BinaryType.boolean_false : lambda _: False,
    BinaryType.int64_zero : lambda _: 0,
    BinaryType.int64_one : lambda _: 1,
    BinaryType.double_zero : lambda _: 0.0,
    BinaryType.double_one : lambda _: 1.0,
    BinaryType.float : _read_float,
    BinaryType.int16 : _read_int16,
    BinaryType.uint16 : _read_uint16,
    BinaryType.int8 : _read_int8,
    BinaryType.uint8 : _read_uint8,
    BinaryType.array_typed_byte_length : _read_array_typed_byte_size,
    BinaryType.array_typed_byte_length2 : _read_array_typed_byte_size2,
}


def _read_value_legacy(context: KV3ContextNew):
    value_type, specifier = context.read_type(context)
    reader = _kv3_readers[value_type]
    if reader is None:
        raise NotImplementedError(f"Reader for {value_type!r} not implemented")
    
    value = reader(context)

    if specifier > Specifier.NONE and specifier < Specifier.ENTITY_NAME:
        value = kv3.flagged_value(value, flags=kv3.Flag(specifier.value))

    return value

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
    return BinaryType(data_type), specifier


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
    return BinaryType(data_type), specifier


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


def read_legacy(compressed_buffer: Buffer) -> kv3.ValueType:
    encoding_bytes_le = compressed_buffer.read(16)
    format_bytes_le = compressed_buffer.read(16)  # Skip format bytes
    buffer: Buffer 

    if encoding_bytes_le == kv3.ENCODING_BINARY_UNCOMPRESSED.version.bytes_le:
        buffer = MemoryBuffer(compressed_buffer.read())
    elif encoding_bytes_le == kv3.ENCODING_BINARY_BLOCK_COMPRESSED.version.bytes_le:
        buffer = _legacy_block_decompress(compressed_buffer)
    elif encoding_bytes_le == kv3.ENCODING_BINARY_BLOCK_LZ4.version.bytes_le:
        decompressed_size = compressed_buffer.read_uint32()
        buffer = MemoryBuffer(lz4.block.decompress(compressed_buffer.read(), decompressed_size))
    else:
        raise ValueError("Unsupported Legacy encoding")
    
    # Note: No need to skip 16 bytes here since we already read the format bytes above
    string_count = buffer.read_uint32()
    strings = [buffer.read_ascii_string() for _ in range(string_count)]

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

def read_v1(buffer: Buffer):
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


def read_v2(buffer: Buffer):
    compression_method = buffer.read_uint32()
    compression_dict_id = buffer.read_uint16()
    compression_frame_size = buffer.read_uint16()

    # Validate compression method - should be 0, 1, or 2
    if compression_method not in [0, 1, 2]:
        raise NotImplementedError(f"Invalid KV3 v2 compression method: {compression_method}. Expected 0, 1, or 2. File may be corrupted or format may be different.")

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
        return BinaryType(data_type), specifier

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


def read_v3(buffer: Buffer):
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


def read_v4(buffer: Buffer):
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


def read_v5(buffer: Buffer):
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
                # f = BinaryTypeFlag(context.types_buffer.read_uint8())
            return BinaryType(t & mask), specific_type

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


def zstd_decompress_stream_wrp(data):
    return zstd_decompress_stream(data)


def lz4_decompress_wrp(data, decomp_size):
    return lz4_decompress(data, decomp_size)


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
