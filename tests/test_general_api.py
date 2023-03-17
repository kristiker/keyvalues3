import pytest

import keyvalues3

def test_api_text():
    text_kv3 = keyvalues3.read("tests/documents/example.kv3")
    assert text_kv3.value["boolValue"] == False
    assert text_kv3.format == keyvalues3.KV3_FORMAT_GENERIC

@pytest.mark.skip(reason="Not implemented yet")
def test_api_binary():
    binary_kv3 = keyvalues3.read("tests/documents/example.bkv3")
    assert binary_kv3.value["boolValue"] == False
