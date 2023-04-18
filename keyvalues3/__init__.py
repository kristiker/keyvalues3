"""
Read and write Valve's KeyValues3 format
"""

import os, io, typing
from .keyvalues3 import *
from .kv3file import KV3File
from .binarywriter import BinaryMagics
from .textreader import KV3TextReader
from . import textwriter

__version__ = "0.1a1"
__all__ = [ "read", "write" ]

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
        magic = binary_stream.read(4)
        binary_stream.seek(0)

        if not BinaryMagics.is_defined(magic):
            raise InvalidKV3Magic("Invalid binary KV3 magic: " + repr(magic))
    
        if magic != BinaryMagics.VKV3:
            raise NotImplementedError("Unsupported binary KV3 magic: " + repr(magic))

        return KV3File({"binary": "reader", "todo": "implement"}, original_encoding=ENCODING_BINARY_UNCOMPRESSED)

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

def write(kv3: KV3File | ValueType, path: str | os.PathLike, encoding: Encoding = ENCODING_TEXT, format: Format = FORMAT_GENERIC):
    raise NotImplementedError()
    if not isinstance(kv3, KV3File):
        kv3 = KV3File(kv3, format=format, validate_value=True)

    if encoding == ENCODING_TEXT:
        textwriter.encode(kv3)
    elif encoding == ENCODING_BINARY_UNCOMPRESSED:
       binarywriter.BinaryV1UncompressedWriter(kv3).write(None)
    elif encoding == ENCODING_BINARY_BLOCK_LZ4:
        binarywriter.BinaryLZ4(kv3).write(None)
