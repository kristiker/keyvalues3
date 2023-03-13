
import array
import enum
import keyvalues3 as kv3

class TextWriterOptions:
    def __init__(self, serialize_enums_as_ints: bool = False, no_header: bool = False):
        self.serialize_enums_as_ints = serialize_enums_as_ints
        self.no_header = no_header

def write_text(value: kv3.KV3File | kv3.kv3_types, options: TextWriterOptions = TextWriterOptions()) -> str:
    return write(value, options)

def write(kv3file: kv3.KV3File | kv3.kv3_types, options: TextWriterOptions = TextWriterOptions()) -> str:
    """Write a KV3File or value to UTF-8 Text."""

    encoding = kv3.KV3_ENCODING_TEXT
    format = kv3.KV3_FORMAT_GENERIC
    value = kv3file

    if isinstance(kv3file, kv3.KV3File):
        format = kv3file.format
        value = kv3file.value

    text = ""
    if not options.no_header:
        text += str(kv3.KV3Header(encoding=encoding, format=format)) + "\n"

    def object_serialize(object: kv3.kv3_types, indentation_level = 0, dictionary_object = False) -> str:
        indent = ("\t" * (indentation_level))
        indent_nested = ("\t" * (indentation_level + 1))
        match object:
            case kv3.flagged_value(value, flags):
                if flags & kv3.Flag.multilinestring:
                    return  f'"""\n{value}"""'
                if flags:
                    return f"{flags}:{object_serialize(value)}"
                return object_serialize(value)
            case None:
                return "null"
            case False:
                return "false"
            case True:
                return "true"
            case int():
                return str(object)
            case float():
                return str(round(object, 6))
            case enum.IntEnum():
                if options.serialize_enums_as_ints:
                    return str(object.value)
                return object.name
            case str():
                return '"' + object + '"'
            case list():
                qualifies_for_sameline = len(object) <= 4 and all(isinstance(item, (dict)) == False for item in object)
                if qualifies_for_sameline:
                    return "[" + ", ".join(object_serialize(item) for item in object) + "]"
                s = f"\n{indent}[\n"
                for item in object:
                    s += indent_nested + (object_serialize(item, indentation_level+1) + ",\n")
                return s + indent + "]"
            case dict():
                s = indent + "{\n"
                if dictionary_object:
                    s = "\n" + s
                for key, value in object.items():
                    s += indent_nested + f"{key} = {object_serialize(value, indentation_level+1, dictionary_object=True)}\n"
                return s + indent + "}"
            case array.array():
                return "[ ]" # TODO
            case bytes() | bytearray():
                return f"#[{' '.join(f'{b:02x}' for b in object)}]"
            case _:
                raise TypeError(f"Invalid type {type(object)} for KV3 value.")

    text += object_serialize(value)
    return text
