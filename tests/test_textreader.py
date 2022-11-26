import unittest

import keyvalues3 as kv3
from keyvalues3.textreader import KV3TextReader, kv3grammar

class Test_TextReading(unittest.TestCase):
    default_header = "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"

    def test_parses_bt_config(self):
        with open("tests/documents/bt_config.kv3", "r") as f:
            kv3Nodes = kv3grammar.parse(f.read())
            KV3TextReader().visit(kv3Nodes)
    
    def test_parses_null_kv3(self):
        kv3Nodes = kv3grammar.parse(self.default_header + "null")
        value = KV3TextReader().visit(kv3Nodes)
        self.assertIsNone(value.value)
    
    def test_parses_example_kv3(self):
        with open("tests/documents/example.kv3", "r") as f:
            kv = KV3TextReader().parse(f.read()).value
            import sys
            self.assertEqual(
                kv["multiLineStringValue"],
                rf"""Lorem ipsum \a \b \c \n ' " "" { "ðŸ˜Š" if sys.platform == "win32" else "😊"}""")
            self.assertEqual(kv["emptyMultiLineString"], "")

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
}""".strip().replace(" "*4, "\t")
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