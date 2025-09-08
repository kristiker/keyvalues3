"""
Additional utility functions for binary processing.
"""

from .buffer import Buffer, MemoryBuffer
from dataclasses import dataclass

@dataclass
class KV3Buffers:
    byte_buffer: Buffer
    short_buffer: Buffer | None
    int_buffer: Buffer
    double_buffer: Buffer

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
