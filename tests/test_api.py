import io
import pytest

import keyvalues3

def verify_example(text_kv3: keyvalues3.KV3File):
    assert text_kv3.original_encoding == keyvalues3.ENCODING_TEXT
    assert text_kv3.format == keyvalues3.FORMAT_GENERIC
    assert isinstance(text_kv3.value, dict)
    assert text_kv3.value["boolValue"] == False

    # dict proxy
    assert text_kv3["boolValue"] == False

def test_api_read_from_path():
    text_kv3 = keyvalues3.read("tests/documents/example.kv3")
    verify_example(text_kv3)

    with pytest.raises(keyvalues3.KV3DecodeError, match="Failed to read KV3 file in text mode."):
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
    binary_kv3 = keyvalues3.read("tests/documents/binary/legacy.kv3.bin")
    assert isinstance(binary_kv3.value, dict)
    assert binary_kv3.value["stringValue"] == "hello world"

    binary_kv3 = keyvalues3.read("tests/documents/binary/legacy.lz4.kv3.bin")
    assert isinstance(binary_kv3.value, dict)
    assert binary_kv3.value["stringValue"] == "hello world"

    # kv3 v1
    entitylump = keyvalues3.read("tests/documents/binary/v1.kv3.bin")
    assert entitylump['m_flags'] == 'ENTITY_LUMP_NONE'

    # kv3 v2
    lightmap_query_data = keyvalues3.read("tests/documents/binary/v2.lz4chain.kv3.bin")
    assert lightmap_query_data['vertex_count'] == 4462

    worldnode = keyvalues3.read("tests/documents/binary/v2.zstd.kv3.bin")
    assert worldnode['m_nodeLightingInfo']['m_vLightmapUvScale'][0] == 1.0

    assert ' '.join(f'{b:02X}' for b in lightmap_query_data['vertices'][-4:]) == '0E 82 C6 4C'
    assert ' '.join(f'{b:02X}' for b in lightmap_query_data['indices'][-4:]) == '6C 11 00 00'

    # kv3 v3
    red2 = keyvalues3.read("tests/documents/binary/v3.lz4.kv3.bin")
    assert red2['m_SearchableUserData']['LightSim_DiffuseAlbedoTexture'] == "dev/helper/testgrid_color_tga_9e9cdde1.vtex"

    # a bad magic
    with pytest.raises(keyvalues3.InvalidKV3Magic, match="Invalid binary KV3 magic: b'VDF3'"):
        keyvalues3.read(io.BytesIO(b"VDF3\x01\x03\x03\x07"))

def test_api_write():
    my_object = {
        "_class": "HelloWorld",
    }

    with io.BytesIO() as my_stream:
        keyvalues3.write(my_object, my_stream)

    with io.StringIO() as my_stream:
        keyvalues3.write(my_object, my_stream)

    import tempfile
    with tempfile.TemporaryFile("w") as fp: keyvalues3.write(my_object, getattr(fp, "file", fp))
    with tempfile.TemporaryFile("wb") as fp: keyvalues3.write(my_object, getattr(fp, "file", fp))

    null_VKV = b'VKV\x03\x00\x05\x86\x1b\xd8\xf7\xc1@\xad\x82u\xa4\x82g\xe7\x14|\x16\x12t\xe9\x06\x98F\xaf\xf2\xe6>\xb5\x907\xe7\x00\x00\x00\x00\x01\xFF\xFF\xFF\xFF'
    with io.BytesIO(null_VKV) as my_stream:
        keyvalues3.write(
            None,
            my_stream,
            keyvalues3.ENCODING_BINARY_UNCOMPRESSED
        )
        assert my_stream.getvalue() == null_VKV
