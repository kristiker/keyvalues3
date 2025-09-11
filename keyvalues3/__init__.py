"""
Read and write Valve's KeyValues3 format
"""

import os, io, typing
from .keyvalues3 import *
from .kv3file import KV3File
from .binarywriter import BinaryMagics
from . import binarywriter
from .textreader import KV3TextReader
from . import textwriter
from .binaryreader import read_valve_keyvalue3
from .utils import MemoryBuffer

__version__ = "0.4"
__all__ = [ "read", "write" ]

#region: read

@typing.overload
def read(text_stream: typing.TextIO) -> KV3File:
    """Read a text KV3 stream."""

@typing.overload
def read(binary_stream: typing.BinaryIO) -> KV3File:
    """Read a binary KV3 stream."""

@typing.overload
def read(path: str | os.PathLike) -> KV3File:
    """
    Read a text or binary KV3 file from a path.

    If a binary magic is present, read in binary mode, otherwise text.

    Raises:
        KV3DecodeError: Error decoding in any of the modes.
    """

def read(path_or_stream: str | os.PathLike | typing.IO) -> KV3File:

    def read_binary(binary_stream: typing.BinaryIO):
        # Read all data from stream
        data = binary_stream.read()
        binary_stream.seek(0)

        # Use the binary reader to parse the data
        buffer = MemoryBuffer(data)

        # Check magic
        magic = buffer.read(4)
        if not BinaryMagics.is_defined(magic):
            raise InvalidKV3Magic("Invalid binary KV3 magic: " + repr(magic))

        # Reset buffer position for read_valve_keyvalue3
        buffer.seek(0)
        value = read_valve_keyvalue3(buffer)
        buffer.seek(4)  # Skip magic

        # Determine encoding based on the binary format
        magic_enum = BinaryMagics(magic)
        if magic_enum == BinaryMagics.VKV3:
            # VKV3 can be uncompressed, block compressed, or LZ4
            encoding_bytes = buffer.read(16)

            if encoding_bytes == ENCODING_BINARY_UNCOMPRESSED.version.bytes_le:
                original_encoding = ENCODING_BINARY_UNCOMPRESSED
            elif encoding_bytes == ENCODING_BINARY_BLOCK_LZ4.version.bytes_le:
                original_encoding = ENCODING_BINARY_BLOCK_LZ4
            elif encoding_bytes == ENCODING_BINARY_BLOCK_COMPRESSED.version.bytes_le:
                original_encoding = ENCODING_BINARY_BLOCK_COMPRESSED
            else:
                original_encoding = ENCODING_BINARY_UNCOMPRESSED
        else:
            # For newer formats (KV3_01-KV3_05), encoding guid is no longer stored
            original_encoding = ENCODING_BINARY_NEW

        format = UUID(bytes_le=buffer.read(16))
        return KV3File(value, format, original_encoding=original_encoding)

    def read_text(text_stream: typing.TextIO):
        return KV3TextReader().parse(text_stream.read())

    if isinstance(path_or_stream, io.TextIOBase):
        return read_text(path_or_stream)
    elif isinstance(path_or_stream, io.BufferedIOBase):
        return read_binary(path_or_stream)

    with open(path_or_stream, "rb") as fp:
        try:
            rv = read_binary(fp)
        except InvalidKV3Magic as not_binary_error:
            try:
                rv = read_text(io.TextIOWrapper(fp, encoding="utf-8"))
            except KV3DecodeError as text_error:
                text_for_sure = "<!--" in (binary_err_str:=str(not_binary_error))
                if (text_for_sure):
                    raise text_error
                raise KV3DecodeError(
                    "Failed to read KV3 file in text mode (binary magic didn't even match). " + str(text_error)
                ) from text_error
        return rv

#endregion

#region: write

def write(kv3: KV3File | ValueType, path_or_stream: str | os.PathLike | typing.IO, encoding: Encoding = ENCODING_TEXT, *,
          format: Format = FORMAT_GENERIC,
          use_original_encoding: bool = False
    ):
    """
    Write a KV3File to a file or stream.

    Args:
        kv3: The KV3File or KV3 value to write.
        path_or_stream: The file path to write to. Or a text/binary stream.
        encoding: The encoding to use.

        format: If a raw kv3 value is passed, this is the format to build it with. Default is 'generic'.
        use_original_encoding: If a kv3 file is passed, use its original encoding.
    """

    if not isinstance(kv3, KV3File):
        kv3 = KV3File(kv3, format=format, validate_value=True)

    if use_original_encoding:
        encoding = kv3file.original_encoding
        if encoding is None:
            raise ValueError("Cannot use original encoding if provided kv3 doesn't have one.")

    # TODO: clean this up with a context manager
    fp = None
    is_file = False

    match path_or_stream:
        case io.IOBase():
            fp = path_or_stream
        case str():
            fp = open(path_or_stream, "wb")
            is_file = True
        case _:
            raise TypeError("Argument path_or_stream must be a path or stream")

    if encoding == ENCODING_TEXT:
        text_result = textwriter.encode(kv3)
        if isinstance(fp, io.TextIOBase):
            fp.write(text_result)
        else:
            fp.write(text_result.encode("utf-8"))
    else:
        if isinstance(fp, io.TextIOBase):
            raise TypeError("Cannot write binary KV3 to a text stream. If this is a file, please open it in binary mode ('wb').")
        if encoding == ENCODING_BINARY_UNCOMPRESSED:
            binarywriter.BinaryV1UncompressedWriter(kv3).write(fp)
        elif encoding == ENCODING_BINARY_BLOCK_LZ4:
            binarywriter.BinaryLZ4(kv3).write(fp)
        else:
            raise NotImplementedError(f"Encoding type {encoding} not implemented.")

    if is_file:
        fp.close()

#endregion

def from_value(data: dict | list | str | int | float | bool | None) -> KV3File:
    """
    Create a KV3File from a dictionary or other type of value.
    """
    return KV3File(data, validate_value=False)
