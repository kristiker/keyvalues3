import unittest

import keyvalues3 as kv3
from keyvalues3.textreader import KV3TextReader, KV3TextReaderNoHeader, kv3grammar
import keyvalues3.textwriter as kv3textwriter

default_header = "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"

# pyright: reportOptionalMemberAccess=false, reportOptionalSubscript=false

class Test_TextReading(unittest.TestCase):

    def test_parses_null_kv3(self):
        kv3Nodes = kv3grammar.parse(default_header + "null")
        value = KV3TextReader().visit(kv3Nodes)
        self.assertIsNone(value.value)
    
    def test_parses_crlf_header(self):
        value = KV3TextReader().parse(default_header.strip() + "\r\n" + "null")
        self.assertIsNone(value.value)

    def test_parses_bt_config(self):
        with open("tests/documents/bt_config.kv3", "r") as f:
            kv3Nodes = kv3grammar.parse(f.read())
            KV3TextReader().visit(kv3Nodes)
    
    def test_parses_example_kv3(self):
        with open("tests/documents/example.kv3", "r", encoding="utf-8") as f:
            kv = KV3TextReader().parse(f.read()).value
            assert isinstance(kv, dict)
            self.assertEqual(
                kv["multiLineStringValue"].value,
                r"""Lorem ipsum \a \b \c \n ' " "" 😊
""")
            self.assertIsInstance(kv["emptyMultiLineString"], kv3.flagged_value)
            self.assertEqual(kv["emptyMultiLineString"].value, "")
            self.assertEqual(kv["emptyMultiLineString"].flags, kv3.Flag.multilinestring)

    def test_parses_example_kv3_no_header(self):
        with open("tests/documents/example_noheader.kv3", "r", encoding="utf-8") as f:
            kv = KV3TextReaderNoHeader().parse(f.read())
            self.assertEqual(kv["foo"], "bar")

    def testflagged_value_base(self):
        self.assertEqual(
            KV3TextReader().parse(default_header + "resource:null").value,
            kv3.flagged_value(value=None, flags=kv3.Flag.resource)
        )
        self.assertEqual(
            KV3TextReader().parse(default_header + "resource_name:{a=2}").value,
            kv3.flagged_value(value={"a":2}, flags=kv3.Flag.resource_name)
        )
    
    def testflagged_value_multi(self):
        self.assertEqual(
            KV3TextReader().parse(default_header + "resource|subclass:null").value,
            kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
        )
        self.assertEqual(
            KV3TextReader().parse(default_header + "subclass|resource:null").value,
            kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
        )
    
    def test_binary_blob_reading(self):
        self.assertEqual(
            KV3TextReader().parse(default_header + "#[00 01 02 03]").value,
            bytes(b"\x00\x01\x02\x03")
        )
        self.assertEqual(
            KV3TextReader().parse(default_header + "#[DEADBEEF]").value,
            bytes(b"\xDE\xAD\xBE\xEF")
        )
    
    def test_multiline_strngs(self):
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '"""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '""""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '"""""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '""""""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '""" """')
        #with self.assertRaises(Exception): KV3TextReader().parse(default_header + '"""\r"""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '"""a\n"""')
        with self.assertRaises(Exception): KV3TextReader().parse(default_header + '"""a\n\n"""')

        assert KV3TextReader().parse(default_header + '"""\n"""').value == ""
        assert KV3TextReader().parse(default_header + '"""\r\n"""').value == ""
        assert KV3TextReader().parse(default_header + '"""\na"""').value == "a"
        assert KV3TextReader().parse(default_header + '"""\na\n"""').value == "a\n"


class Test_TextReadWriting(unittest.TestCase):
    kv3text = """
{
    boolValue = false
    intValue = 128
    doubleValue = 64.0
    stringValue = "hello world"
    stringThatIsAResourceReference = resource:"particles/items3_fx/star_emblem.vpcf"
    stringThatIsAResourceAndSubclass = resource|subclass:"particles/items3_fx/star_emblem.vpcf"
    multiLineStringValue = ""\"
""\"
    arrayValue = [1, 2]
    objectValue = 
    {
        n = 5
        s = "foo"
    }
}""".strip().replace(" "*4, "\t")
    
    def test_prints_back_same_kv3_header(self):
        value = KV3TextReader().parse(default_header + self.kv3text)
        self.assertEqual(default_header + self.kv3text, kv3textwriter.encode(value))

    def test_prints_back_same_kv3_no_header(self):
        value = KV3TextReaderNoHeader().parse(self.kv3text)
        self.assertEqual(self.kv3text, kv3textwriter.encode(value, kv3textwriter.KV3EncoderOptions(no_header=True)))



import pytest
from pathlib import Path
import shutil
import subprocess
import warnings

dota2_path =  Path(r'D:\Games\steamapps\common\dota 2 beta')

resourcecompiler = dota2_path / 'game' / 'bin' / 'win64' / 'resourcecompiler.exe'
workdir = dota2_path / 'content' / 'dota_addons' / 'test_pykv3_parity'
gamedir = dota2_path / 'game' / 'dota_addons' / 'test_pykv3_parity'

@pytest.fixture
def setup_teardown():
    if resourcecompiler.is_file():
        workdir.mkdir(parents=True, exist_ok=True)
    yield
    if resourcecompiler.is_file():
        vpfc_files.clear()
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(gamedir, ignore_errors=True)

kv3_files = []
vpfc_files = []

for kv3file in Path("tests/documents").glob('*.kv3'):
    assumed_valid = kv3file.stem != "not_kv3"
    no_header = "noheader" in kv3file.stem
    parameters = (assumed_valid, no_header)
    
    kv3_files.append((kv3file, *parameters))
    if resourcecompiler.is_file():
        vpcf_to_compile = (workdir / kv3file.name).with_suffix('.vpcf')
        shutil.copy(kv3file, vpcf_to_compile)
        vpfc_files.append((vpcf_to_compile, *parameters))

#@pytest.mark.skipif(resourcecompiler.is_file() == True, reason="prioritizing [test_parity]")
@pytest.mark.parametrize("file,assumed_valid,no_header", kv3_files, ids=[f"'{f.name}'-{v}{n}" for f, v, n in kv3_files])
def test_reads_kv3_file_as_expected(file: Path, assumed_valid: bool, no_header: bool):
    with open(file, "r") as f:
        reader = KV3TextReaderNoHeader() if no_header else KV3TextReader()
        if assumed_valid:
            reader.parse(f.read())
            return
        with pytest.raises(Exception):
            reader.parse(f.read())

@pytest.mark.skipif(resourcecompiler.is_file() == False, reason="resourcecompiler not available")
@pytest.mark.parametrize("file,assumed_valid,no_header", vpfc_files, ids=[f"'{f.name}'-{v}{n}" for f, v, n in vpfc_files])
def test_parity(file: Path, assumed_valid: bool, no_header: bool):
    """Check parity with resourcecompiler"""
    result = subprocess.run([resourcecompiler, "-f", file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if not b"a root object of type 'CParticleSystemDefinition'" in result.stdout:
        if no_header: # these do not compile
            return
        if assumed_valid:
            warnings.warn(f"File '{file.name}' was assumed valid, but resourcecompiler says it isn't. {result.stdout.decode('utf-8')}", UserWarning)
        
        # if resourcecompiler failed, we should fail too
        with pytest.raises(kv3.KV3DecodeError):
            with open(file, "r") as f:
                KV3TextReader().parse(f.read())
    else:
        if not assumed_valid:
            warnings.warn(f"File '{file.name}' was assumed invalid, but resourcecompiler says it's fine.", UserWarning)
        
        # if resourcecompiler succeeded, we should succeed too
        with open(file, "r") as f:
            KV3TextReader().parse(f.read())
