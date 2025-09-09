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
    """LZ4 chain decoder that maintains a continuous output buffer for dictionary compression"""
    
    def __init__(self, block_size: int, extra_blocks: int = 0):
        """Initialize a new LZ4ChainDecoder
        
        Args:
            block_size: The size of each block to be decompressed
            extra_blocks: Number of extra blocks to allocate in the output buffer
        """
        # Ensure block size is at least 1024 and a power of two
        self.block_size = max(block_size, 1024)
        if self.block_size & (self.block_size - 1) != 0:
            self.block_size = 1 << (self.block_size - 1).bit_length()
            
        # Calculate output buffer size: 64KB dict + extra blocks + padding
        output_length = (1024 * 64) + (1 + extra_blocks) * self.block_size + 32
        self.output_buffer = bytearray(output_length)
        self.output_index = 0
        self.frame_size = block_size
        
    def prepare(self, block_size: int) -> None:
        """Prepare the output buffer for the next block
        
        Args:
            block_size: Size of the next block to be decompressed
            
        Raises:
            ValueError: If the block size is too large
        """
        if self.output_index + block_size <= len(self.output_buffer):
            return
            
        # Keep last 64KB as dictionary
        dict_start = max(self.output_index - (1024 * 64), 0)
        dict_size = self.output_index - dict_start
        
        # Move dictionary to start of buffer
        self.output_buffer[0:dict_size] = self.output_buffer[dict_start:self.output_index]
        self.output_index = dict_size
        
    def decode(self, src: bytes, block_size: int = 0) -> int:
        """Decode a compressed block using LZ4
        
        Args:
            src: Compressed data
            block_size: Size of block to decompress into, or 0 to use frame_size
            
        Returns:
            Number of bytes decompressed
            
        Raises:
            ValueError: If input data is too large or decompression fails
        """
        if block_size <= 0:
            block_size = self.frame_size
            
        self.prepare(block_size)
        
        # Decompress using dictionary from output buffer
        decompressed = lz4.block.decompress(
            src, 
            block_size,
            dict=bytes(self.output_buffer[:self.output_index]) if self.output_index > 0 else None
        )
        
        decoded_size = len(decompressed)
        if decoded_size > 0:
            self.output_buffer[self.output_index:self.output_index + decoded_size] = decompressed
            self.output_index += decoded_size
            
        return decoded_size
        
    def drain(self, dst: bytearray, offset: int, size: int) -> None:
        """Copy data from the output buffer into the destination buffer
        
        Args:
            dst: Destination buffer to copy into
            offset: Offset from end of output buffer
            size: Number of bytes to copy
            
        Raises:
            ValueError: If offset or size are invalid
        """
        end_offset = self.output_index + offset
        if (end_offset < 0 or 
            size > len(dst) or
            end_offset + size > self.output_index):
            raise ValueError("Invalid offset or size")
            
        dst[0:size] = self.output_buffer[end_offset:end_offset + size]
        
    def decode_and_drain(self, src: bytes, dst: bytearray) -> int:
        """Decode compressed data and drain directly into destination buffer
        
        Args:
            src: Compressed source data
            dst: Destination buffer for decompressed data
            
        Returns:
            Number of bytes decompressed
            
        Raises:
            ValueError: If decompression fails or buffer overflows
        """
        decoded = self.decode(src, 0)
        if decoded > len(dst):
            print(f"Decode buffer overflow: {decoded}>{len(dst)}")
            raise ValueError("Decode buffer overflow")
            
        self.drain(dst, -decoded, decoded)
        return decoded

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
                         compression_frame_size: int) -> bytes:
    """Decompress a chain of LZ4 blocks
    
    Args:
        buffer: Input buffer containing compressed data
        decompressed_block_sizes: List of expected decompressed sizes for each block
        compressed_block_sizes: List of compressed sizes for each block
        compression_frame_size: Frame size used for compression
        
    Returns:
        Decompressed data as bytes
        
    Raises:
        ValueError: If decompression fails or buffer sizes don't match
    """
    # Calculate total decompressed size and create output buffer
    total_size = sum(decompressed_block_sizes)
    out_buffer = bytearray(total_size)
    out_pos = 0
    
    # Create decoder with frame size and enough space for all blocks
    cd = LZ4ChainDecoder(compression_frame_size, len(decompressed_block_sizes))
    
    for block_size in decompressed_block_sizes:
        remaining = block_size
        while buffer.tell() < buffer.size() and remaining > 0:
            compressed_size = compressed_block_sizes.pop(0)
            block = buffer.read(compressed_size)
            
            # Create a slice of the output buffer for this block
            block_slice = memoryview(out_buffer)[out_pos:out_pos + remaining]
            
            # Decode directly into the output slice
            decoded = cd.decode_and_drain(block, block_slice)
            actual_size = min(decoded, remaining)
            
            out_pos += actual_size
            remaining -= actual_size
            
    return bytes(out_buffer)
