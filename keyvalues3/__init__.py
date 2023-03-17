import os, io, typing
from .keyvalues3 import *
from .binarywriter import BinaryMagics
from .textreader import KV3TextReader
from . import textwriter

__all__ = [ "read", "write" ]

@typing.overload
def read(text_stream: typing.TextIO) -> KV3File:
    """Read a text KV3 file from a stream."""

@typing.overload
def read(binary_stream: typing.BinaryIO) -> KV3File:
    """Read a binary KV3 file from a stream."""

@typing.overload
def read(path: str | os.PathLike) -> KV3File:
    """Read a binary or text KV3 file from a path."""

def read(path_or_stream: str | os.PathLike | typing.IO) -> KV3File:

    def read_binary(binary_stream: typing.BinaryIO):
        magic = binary_stream.read(4)
        binary_stream.seek(0)
        if magic == BinaryMagics.VKV3.value:
            return KV3File({"binary": "reader", "todo": "implement"})
        raise InvalidKV3Magic("Invalid binary KV3 magic: " + repr(magic))

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
                raise KV3DecodeError(
                    "Failed to read KV3 file in both text and binary modes." +
                    f"\n\tBinary: {not_binary_error}" +
                    f"\n\tText: {text_error}"
                ) from text_error
        return rv

def write(kv3: KV3File | kv3_types, path: str | os.PathLike, encoding: Encoding = KV3_ENCODING_TEXT, format: Format = KV3_FORMAT_GENERIC):
    raise NotImplementedError()
    if not isinstance(kv3, KV3File):
        kv3 = KV3File(kv3, format=format, validate_value=True)

    if encoding == KV3_ENCODING_TEXT:
        textwriter.encode(kv3)
    elif encoding == KV3_ENCODING_BINARY_UNCOMPRESSED:
       binarywriter.BinaryV1UncompressedWriter(kv3).write(None)
    elif encoding == KV3_ENCODING_BINARY_BLOCK_LZ4:
        binarywriter.BinaryLZ4(kv3).write(None)
