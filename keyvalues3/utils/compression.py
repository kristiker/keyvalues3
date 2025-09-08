"""
Compression utility functions for LZ4 and ZSTD decompression.
"""

import lz4.block
import zstandard as zstd
from .buffer import Buffer, MemoryBuffer, WritableMemoryBuffer

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
