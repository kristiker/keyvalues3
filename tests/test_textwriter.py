
import dataclasses, uuid
from keyvalues3 import KV3File, KV3Header, Encoding, Format, textwriter

default_header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'

def test_text_writer_header():
    custom_header = KV3Header(Encoding('text2', uuid.UUID(int = 0)), Format('generic2', uuid.UUID(int = 1)))
    expected_text = '<!-- kv3 encoding:text2:version{00000000-0000-0000-0000-000000000000} format:generic2:version{00000000-0000-0000-0000-000000000001} -->'
    assert str(custom_header) == expected_text

def test_text_writer_writes_null():
    null_kv3 = KV3File(None)
    expected_text = default_header + "\nnull\n"
    assert textwriter.encode(null_kv3) == expected_text

def test_text_writer_writes_empty_list():
    empty_list_kv3 = KV3File([])
    expected_text = default_header + "\n[]\n"
    assert textwriter.encode(empty_list_kv3) == expected_text

def test_text_writer_writes_empty_string():
    empty_string_kv3 = KV3File("")
    expected_text = default_header + '\n""\n'
    assert textwriter.encode(empty_string_kv3) == expected_text

def test_text_writer_writes_int():
    int_kv3 = KV3File(1337)
    expected_text = default_header + "\n1337\n"
    assert textwriter.encode(int_kv3) == expected_text

def test_text_writer_writes_float():
    float_kv3 = KV3File(1337.1337)
    expected_text = default_header + "\n1337.1337\n"
    assert textwriter.encode(float_kv3) == expected_text

def test_text_writer_writes_bool():
    true_kv3 = KV3File(True)
    false_kv3 = KV3File(False)
    expected_text_true = default_header + "\ntrue\n"
    expected_text_false = default_header + "\nfalse\n"
    assert textwriter.encode(true_kv3) == expected_text_true
    assert textwriter.encode(false_kv3) == expected_text_false

def test_text_writer_list_indentation():
    data = {
        "use_distance_volume_mapping_curve": True,
        "distance_volume_mapping_curve":
        [
            [ 0, 1, 0, 0, 2, 3, ],
            [ 100, 1, 0, 0, 2, 3, ],
            [ 900, 0.5, 0, 0, 2, 3, ],
            [ 1300, 0.04, 0, 0, 2, 3, ],
            [ 1700, 0, 0, 0, 2, 3, ],
        ] 
    }

    # the kv3 should be formatted roughly like above
    expected_soundevent_kv3 = util_make_indented_kv3("""
    {
        use_distance_volume_mapping_curve = true
        distance_volume_mapping_curve = 
        [
            [0, 1, 0, 0, 2, 3],
            [100, 1, 0, 0, 2, 3],
            [900, 0.5, 0, 0, 2, 3],
            [1300, 0.04, 0, 0, 2, 3],
            [1700, 0, 0, 0, 2, 3],
        ]
    }
    """)

    kv3 = KV3File(data)
    kv3_text = textwriter.encode(kv3)
    #print(kv3_text)
    assert kv3_text == expected_soundevent_kv3

def test_text_writer_writes_dict():
    empty_dict_kv3 = KV3File({})
    expected_empty_dict_text = default_header + "\n{\n}\n"
    assert textwriter.encode(empty_dict_kv3) == expected_empty_dict_text

    @dataclasses.dataclass
    class MyKV3Format:
        a: str = 'asd asd'
        b: dict = dataclasses.field(default_factory=lambda: {"inner_b":3})
        c: list = dataclasses.field(default_factory=lambda: ["listed_text1", "listed_text2"])

    dataclass_kv3 = KV3File(MyKV3Format())
    dict_kv3 = KV3File(
        {
            'a': 'asd asd',
            'b':
            {
                "inner_b": 3
            },
            'c': ["listed_text1", "listed_text2"]
        }
    )
    expected_dict_kv3_text = util_make_indented_kv3("""
        {
            a = "asd asd"
            b = 
            {
                inner_b = 3
            }
            c = 
            [
                "listed_text1",
                "listed_text2",
            ]
        }
    """, 2)
    assert textwriter.encode(dict_kv3) == expected_dict_kv3_text
    assert textwriter.encode(dataclass_kv3) == expected_dict_kv3_text

    assert '"key with spaces"' in textwriter.encode({"key with spaces": 5})
    assert '"key.co.uk" =' in textwriter.encode({"key.co.uk": 5})

    assert (key:="escaped \" quote in key") in textwriter.encode({key: 5})
    assert (key:="escaped \n newline in key") in textwriter.encode({key: 5})
    assert (key:="escaped \\ backslash in key") in textwriter.encode({key: 5})

    assert (value:="foo \"bar\"") in textwriter.encode({"key": value})


def util_make_indented_kv3(code_kv3: str, code_indentation_level=1) -> str:
    return (default_header + "\n" + code_kv3
            .strip() # undo detached triple quotes
            .replace(" "*4, "\t") # convert to tabs
            .replace("\n"+"\t"*code_indentation_level, "\n") # remove added indent
            + "\n" # add newline at end
    )
