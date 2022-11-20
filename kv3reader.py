import parsimonious

import keyvalues3 as kv3
import uuid
import itertools

kv3grammar = parsimonious.Grammar(
    """
    kv3 = header ws* data ws*
    header = "<!-- kv3 " encoding " " format " -->\\n"
        encoding = "encoding:" identifier ":version" guid
        format = "format:" identifier ":version" guid
            guid = ~"{[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}}"i

    data = (object / object_flagged)

    array = "[" items "]"
        items = (ws* data ws* ",")* ws* (data ws*)?
    dict = "{" pair* "}"
        pair = ws? key ws? "=" ws* data ws*
            key = (identifier / string)

    object_flagged = (flags ":") object
        flags = (identifier "+")* identifier
    object = null / true / false / float / int / multiline_string / string / dict / array / binary_blob
        null = "null"
        true = "true"
        false = "false"
        int = ~"-?[0-9]+"
        float = ~"-?[0-9]+\\.[0-9]+"
        string = ~'"[^"]*"'
        multiline_string = triple_quote triple_quote
            triple_quote = '\"\"\"'
        binary_blob = '#[' ~'[0-9a-f]{2}' ']'

    ws = ~r"\\s+" / single_line_comment / multi_line_comment
    single_line_comment = ~r"//.*?\\n"
    multi_line_comment = ~"/\\*[^*]*\\*+(?:[^/*][^*]*\\*+)*/"

    identifier = ~"[a-zA-Z0-9_]+"i
    """
)



class KV3TextReader(parsimonious.NodeVisitor):
    grammar = kv3grammar
    unwrapped_exceptions: tuple[type[BaseException], ...] = (ValueError)
    class list_of_nodes(list):
        pass
    class NonObject(object):
        pass
    
    non_object = NonObject()
    
    def parse(self, text: str) -> kv3.KV3File:
        """Parse the given text into a KV3File object."""
        return super().parse(text)
    
    loads = parse
    read = parse

    def visit(self, node) -> kv3.KV3File:
        return super().visit(node)
    
    @staticmethod
    def is_object(node):
        return node is not KV3TextReader.non_object and not isinstance(node, KV3TextReader.list_of_nodes)

    def visit_kv3(self, node, visited_children: list[kv3.KV3Header | kv3.kv3_types]) -> kv3.KV3File:
        header = visited_children[0]
        if not isinstance(header, kv3.KV3Header):
            raise ValueError("kv3 has invalid header")
        try:
            data = next(data for data in visited_children[1:] if self.is_object(data))
        except StopIteration:
            raise ValueError("kv3 contains no data")
        else:
            return kv3.KV3File(value = data, format = header.format)

    def visit_header(self, _, visited_children) -> kv3.KV3Header:
        return kv3.KV3Header(encoding=visited_children[1], format=visited_children[3])
    
    def visit_encoding(self, _, visited_children) -> kv3.Encoding:
        return kv3.Encoding(name=visited_children[1].text, version=uuid.UUID(visited_children[3].text))
    def visit_format(self, _, visited_children) -> kv3.Format:
        return kv3.Format(name=visited_children[1].text, version=uuid.UUID(visited_children[3].text))

    def visit_data(self, node, visited_children) -> kv3.kv3_types:
        return visited_children[0]

    def visit_object(self, _, visited_children) -> kv3.kv3_types:
        return visited_children[0]
    
    def visit_object_flagged(self, _, visited_children) -> kv3.flagged_value:
        return kv3.flagged_value(value=visited_children[1], flags=visited_children[0][0])
    
    def visit_flags(self, _, visited_children):
        flag = kv3.Flag(0)
        if isinstance(visited_children[0], KV3TextReader.list_of_nodes):
            for child in visited_children[0]:
                flag |= kv3.Flag[child[0].text]
        return flag | kv3.Flag[visited_children[1].text]
    
    def visit_null(self, node, visited_children): return None
    def visit_true(self, node, visited_children): return True
    def visit_false(self, node, visited_children): return False
    def visit_int(self, node, visited_children): return int(node.text)
    def visit_float(self, node, visited_children): return float(node.text)
    def visit_string(self, node, visited_children): return node.text[1:-1]
    def visit_multiline_string(self, node, visited_children): return kv3.str_multiline(node.text[3:-3])
    #def visit_binary_blob(self, node, visited_children): return bytes.fromhex(node.text[2:-1])
    
    def visit_array(self, node, visited_children) -> list:
        return visited_children[1]
    
    def visit_items(self, node, visited_children) -> list:
        rv = []
        for child in itertools.chain(visited_children[0], visited_children[2]):
            if child is None:
                continue
            it = (item for item in child if self.is_object(item))
            rv.append(next(it))
        return rv

    def visit_dict(self, node, visited_children) -> dict:
        rv = {}
        for kvp in visited_children[1]:
            rv[kvp[0]] = kvp[1]
        return rv
    
    def visit_pair(self, node, visited_children) -> tuple[str, None | object | kv3.flagged_value]:
        it = (child for child in visited_children if self.is_object(child))
        return next(it), next(it)
    
    def visit_key(self, node, _) -> str:
        return node.text

    def generic_visit(self, node, visited_children):
        """ The generic visit method. """
        if node.expr_name == 'ws':
            return None
        if len(visited_children):
            return KV3TextReader.list_of_nodes(visited_children)
        return node if node.expr_name else KV3TextReader.non_object

if __name__ == '__main__':
    import unittest

    class Test_KV3Grammar(unittest.TestCase):
        default_header = "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"
        def test_parses_bt_config(self):
            with open("tests/bt_config.kv3", "r") as f:
                kv3Nodes = kv3grammar.parse(f.read())
                KV3TextReader().visit(kv3Nodes)
        def test_parses_null_kv3(self):
            kv3Nodes = kv3grammar.parse(self.default_header + "null")
            value = KV3TextReader().visit(kv3Nodes)
            self.assertIsNone(value.value)
        
        def test_parses_kv3(self):
            kv3text = self.default_header + """
            {
                boolValue = false
                intValue = 128
                doubleValue = 64.000000
                stringValue = "hello world"
                stringThatIsAResourceReference = resource:"particles/items3_fx/star_emblem.vpcf"
                multiLineStringValue = ""\"""\"
                arrayValue =
                [
                    1,
                    2
                ]
                objectValue =
                {
                    n = 5
                    s = "foo"
                }
                // single line comment
                /* multi
                line
                comment */
            }"""
            value = KV3TextReader().parse(kv3text)

        def test_prints_back_same_kv3(self):
            kv3text = self.default_header + """
            {
                boolValue = false
                intValue = 128
                doubleValue = 64.0
                stringValue = "hello world"
                stringThatIsAResourceReference = resource:"particles/items3_fx/star_emblem.vpcf"
                stringThatIsAResourceAndSubclass = resource+subclass:"particles/items3_fx/star_emblem.vpcf"
                multiLineStringValue = ""\"""\"
                arrayValue = [1, 2]
                objectValue = 
                {
                    n = 5
                    s = "foo"
                }
            }""".strip().replace(" "*4, "\t").replace("\t"*3, "")
            value = KV3TextReader().parse(kv3text)
            self.assertEqual(str(value), kv3text)

        def testflagged_value_base(self):
            self.assertEqual(
                KV3TextReader().parse(self.default_header + "resource:null").value,
                kv3.flagged_value(value=None, flags=kv3.Flag.resource)
            )
            self.assertEqual(
                KV3TextReader().parse(self.default_header + "resourcename:{a=2}").value,
                kv3.flagged_value(value={"a":2}, flags=kv3.Flag.resourcename)
            )
        
        def testflagged_value_multi(self):
            self.assertEqual(
                KV3TextReader().parse(self.default_header + "resource+subclass:null").value,
                kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
            )
            self.assertEqual(
                KV3TextReader().parse(self.default_header + "subclass+resource:null").value,
                kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
            )

    unittest.main()
