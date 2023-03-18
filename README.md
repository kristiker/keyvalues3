## keyvalues3
KeyValues3 is a Valve developed data format. It is similar in structure to JSON, but supports binary encodings, versioning, and data annotations. The text syntax also has some minor ergonomic improvements (support for single- and multi-line comments, trailing commas, and multi-line strings.)

## Usage
```py
>>> import keyvalues3 as kv3
>>> kv3.read("tests/documents/bt_config.kv3")
KV3File(value={'default': {'aim_target_acquisition_lerp_time': 0.7, 'aim_target_acquisition_lerp_time_deviation': ...)

>>> with open("tests/documents/bt_config.kv3", "r", encoding="utf-8") as fp:
...     file = keyvalues3.read(fp)
...     print(file.original_encoding)
...     print(file.format)
...     print(file.value.keys())
...     print(file.value["elite"]["reaction_time"])

Format(name='generic', version=UUID('7412167c-06e9-4698-aff2-e63eb59037e7'))
Encoding(name='text', version=UUID('e21c7f3c-8a33-41c5-9977-a76d3a32aa0d'))
dict_keys(['default', 'low', 'fair', 'normal', 'tough', 'hard', 'very_hard', 'expert', 'elite'])
0.12

```

## Install
`pip install git+https://github.com/kristiker/keyvalues3`

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
