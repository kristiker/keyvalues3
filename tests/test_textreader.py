import unittest

import keyvalues3 as kv3
from keyvalues3.textreader import KV3TextReader, kv3grammar

class Test_TextReading(unittest.TestCase):
    default_header = "<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->\n"

    def test_parses_null_kv3(self):
        kv3Nodes = kv3grammar.parse(self.default_header + "null")
        value = KV3TextReader().visit(kv3Nodes)
        self.assertIsNone(value.value)
    
    def test_parses_crlf_header(self):
        value = KV3TextReader().parse(self.default_header.strip() + "\r\n" + "null")
        self.assertIsNone(value.value)

    def test_parses_bt_config(self):
        with open("tests/documents/bt_config.kv3", "r") as f:
            kv3Nodes = kv3grammar.parse(f.read())
            KV3TextReader().visit(kv3Nodes)
    
    def test_parses_example_kv3(self):
        with open("tests/documents/example.kv3", "r", encoding="utf-8") as f:
            kv = KV3TextReader().parse(f.read()).value
            self.assertEqual(
                kv["multiLineStringValue"],
                r"""Lorem ipsum \a \b \c \n ' " "" 😊""")
            self.assertEqual(kv["emptyMultiLineString"], "")

    def test_prints_back_same_kv3(self):
        kv3text = self.default_header + """
{
    boolValue = false
    intValue = 128
    doubleValue = 64.0
    stringValue = "hello world"
    stringThatIsAResourceReference = resource:"particles/items3_fx/star_emblem.vpcf"
    stringThatIsAResourceAndSubclass = resource|subclass:"particles/items3_fx/star_emblem.vpcf"
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
            KV3TextReader().parse(self.default_header + "resource|subclass:null").value,
            kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
        )
        self.assertEqual(
            KV3TextReader().parse(self.default_header + "subclass|resource:null").value,
            kv3.flagged_value(value=None, flags=kv3.Flag.resource|kv3.Flag.subclass)
        )
    
    def test_binary_blob_reading(self):
        self.assertEqual(
            KV3TextReader().parse(self.default_header + "#[00 01 02 03]").value,
            bytes(b"\x00\x01\x02\x03")
        )
        self.assertEqual(
            KV3TextReader().parse(self.default_header + "#[DEADBEEF]").value,
            bytes(b"\xDE\xAD\xBE\xEF")
        )

import pytest
from pathlib import Path
import shutil
import subprocess
import warnings

dota2_path =  Path(r'D:\Games\steamapps\common\dota 2 beta')

resourcecompiler = dota2_path / 'game' / 'bin' / 'win64' / 'resourcecompiler.exe'
workdir = dota2_path / 'content' / 'dota_addons' / 'test_pykv3_parity'
gamedir = dota2_path / 'game' / 'dota_addons' / 'test_pykv3_parity'

if resourcecompiler.is_file():
    workdir.mkdir(parents=True, exist_ok=True)

kv3_files = []
vpfc_files = []

for kv3file in Path("tests/documents").glob('**/*.kv3'):
    assumed_valid = False if kv3file.stem == "not_kv3" else True
    kv3_files.append((kv3file, assumed_valid))
    if resourcecompiler.is_file():
        vpcf_to_compile = (workdir / kv3file.name).with_suffix('.vpcf')
        shutil.copy(kv3file, vpcf_to_compile)
        vpfc_files.append((vpcf_to_compile, assumed_valid))

@pytest.mark.skipif(resourcecompiler.is_file() == True, reason="prioritizing [test_parity]")
@pytest.mark.parametrize("file,assumed_valid", vpfc_files, ids=[f"'{f.name}'-{v}" for f, v in vpfc_files])
def test_reads_kv3_file_as_expected(file: Path, assumed_valid: bool):
    with open(file, "r") as f:
        if assumed_valid:
            KV3TextReader().parse(f.read())
            return
        with pytest.raises(Exception):
            KV3TextReader().parse(f.read())

@pytest.mark.skipif(resourcecompiler.is_file() == False, reason="resourcecompiler not available")
@pytest.mark.parametrize("file,assumed_valid", vpfc_files, ids=[f"'{f.name}'-{v}" for f, v in vpfc_files])
def test_parity(file: Path, assumed_valid: bool):
    """Check parity with resourcecompiler"""
    result = subprocess.run([resourcecompiler, file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0:
        if assumed_valid:
            warnings.warn(f"Resourcecompiler deems '{file.name}' as not valid KV3", UserWarning)
        
        # if resourcecompiler failed, we should fail too
        with pytest.raises(Exception):
            with open(file, "r") as f:
                KV3TextReader().parse(f.read())
    else:
        if not assumed_valid:
            warnings.warn(f"Resourcecompiler deems '{file.name}' as valid KV3", UserWarning)
        
        # if resourcecompiler succeeded, we should succeed too
        with open(file, "r") as f:
            KV3TextReader().parse(f.read())

def test_actual_cleanup():
    vpfc_files.clear()
    if resourcecompiler.is_file():
        shutil.rmtree(workdir, ignore_errors=True)
        shutil.rmtree(gamedir, ignore_errors=True)
