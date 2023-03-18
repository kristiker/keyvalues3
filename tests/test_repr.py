
import uuid
import keyvalues3

def test_api_repr_str():
    kv3 = keyvalues3.KV3File({"test": "object"}, format=keyvalues3.FORMAT_GENERIC)
    assert repr(kv3) == r"KV3File(value={'test': 'object'})"
    assert str(kv3) ==  r"KV3File(value={'test': 'object'})"

    my_format = keyvalues3.Format("vpcf", uuid.uuid4())
    kv3_vpcf = keyvalues3.KV3File({"_class": "CParticleSystemDefinition"}, format=my_format)
    # KV3File({'test': 'value'}, format=Format(name='vpcf', uuid=UUID('a3b4c5d6-e7f8-9a0b-1c2d-3e4f5a6b7c8d')))
    assert repr(kv3_vpcf) == r"KV3File({'_class': 'CParticleSystemDefinition'}, format=" + repr(my_format) + ")"
