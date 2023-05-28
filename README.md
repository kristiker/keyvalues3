## keyvalues3
KeyValues3 is a Valve developed data format. It is similar in structure to JSON, but supports binary encodings, versioning, and data annotations. The text syntax also has some minor ergonomic improvements (support for single- and multi-line comments, trailing commas, and multi-line strings.)

## Usage
```py
import keyvalues3 as kv3
bt_config = kv3.read("tests/documents/bt_config.kv3")

>>> bt_config.keys()
dict_keys(['default', 'low', 'fair', 'normal', 'tough', 'hard', 'very_hard', 'expert', 'elite'])

>>> bt_config["elite"]["reaction_time"]
0.12
```

```py
# The root value is most of the time a dict
>>> type(bt_config.value)
<class 'dict'>

>>> bt_config.original_encoding
Encoding(name='text', version=UUID('e21c7f3c-8a33-41c5-9977-a76d3a32aa0d'))

>>> bt_config.format
Format(name='generic', version=UUID('7412167c-06e9-4698-aff2-e63eb59037e7'))

# To write it back
>>> kv3.write(bt_config, "tests/documents/bt_config.kv3", use_original_encoding=True)

# Write to a stream
>>> import sys
>>> kv3.write({"key": [1,2,3]}, sys.stdout)
<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->
{
        key = [1, 2, 3]
}
```

## Install  [![PyPI version](https://badge.fury.io/py/keyvalues3.svg)](https://badge.fury.io/py/keyvalues3)
```bash
pip install keyvalues3
```

## Supported encodings
| Encoding 👩‍💻 | Read 📖 | Write ✍️ |
| ----------- | :-----: | :-------: |
| Text UTF-8 | Yes ✔️ | Yes ✔️ |
| Text UTF-8 Headerless | Yes ✔️ | Yes ✔️ |
| Binary Uncompressed | No ⛔ | Yes ✔️ |
| Binary LZ4 | No ⛔ | Yes ✔️ |
| Binary (Other newer) | No ⛔ | No ⛔ |

## Credits
Valve Corporation for making KeyValues3.  
[SteamDatabase/ValveResourceFormat](https://github.com/SteamDatabase/ValveResourceFormat/blob/master/ValveResourceFormat/Resource/ResourceTypes/BinaryKV3.cs) for reversing the binary formats.
