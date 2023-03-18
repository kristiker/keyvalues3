import io
import pytest

import keyvalues3

def verify_example(text_kv3: keyvalues3.KV3File):
    assert text_kv3.original_encoding == keyvalues3.ENCODING_TEXT
    assert text_kv3.format == keyvalues3.FORMAT_GENERIC
    assert isinstance(text_kv3.value, dict)
    assert text_kv3.value["boolValue"] == False

def test_api_read_from_path():
    text_kv3 = keyvalues3.read("tests/documents/example.kv3")
    verify_example(text_kv3)

    with pytest.raises(keyvalues3.KV3DecodeError, match="Failed to read KV3 file in both text and binary modes."):
        keyvalues3.read("tests/documents/not_kv3.kv3")

def test_api_read_from_stream():
    with open("tests/documents/example.kv3") as fp:
        text_kv3 = keyvalues3.read(fp)
        verify_example(text_kv3)
    
    with pytest.raises(keyvalues3.KV3DecodeError, match="KV3 Text Rule 'kv3' didn't match at 'invalidkv3'"):
        keyvalues3.read(io.StringIO("invalidkv3"))

    with pytest.raises(keyvalues3.KV3DecodeError, match="KV3 Text Rule 'kv3' didn't match at 'invalidkv3'"):
        keyvalues3.read(io.StringIO("invalidkv3"))
    

def test_api_read_binary():
    binary_kv3 = keyvalues3.read("tests/documents/binary/example.kv3")
    assert isinstance(binary_kv3.value, dict)
    assert binary_kv3.value["binary"] == "reader"

    binary_kv3 = keyvalues3.read("tests/documents/binary/example_lz4.kv3")
    assert isinstance(binary_kv3.value, dict)
    assert binary_kv3.value["binary"] == "reader"

    with pytest.raises(NotImplementedError):
        keyvalues3.read("tests/documents/binary/lightmap_query_data.kv3")

    with pytest.raises(keyvalues3.InvalidKV3Magic, match="Invalid binary KV3 magic: b'VDF3'"):
        keyvalues3.read(io.BytesIO(b"VDF3\x01\x03\x03\x07"))
