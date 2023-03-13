## keyvalues3
KeyValues3 is a Valve developed data format. It is similar in structure to JSON, but supports binary encodings, versioning, and data annotations. The text syntax also has some minor ergonomic improvements (support for single- and multi-line comments, trailing commas, and multi-line strings.)

## Install
Copy the code. Todo: pip

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
