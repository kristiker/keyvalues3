import pytest

import keyvalues3

@pytest.mark.skip(reason="Not implemented yet")
def test_api_use():
    text_kv3 = keyvalues3.read("tests/documents/example.kv3")
    assert text_kv3.value["boolValue"] == False
