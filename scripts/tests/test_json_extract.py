import lib_naan.ghissue

def test_00_extract_json_block():
    md = """
    """
    data = lib_naan.ghissue.extract_json_block_from_markdown(md)
    assert data is None

def test_01_extract_json():
    md = """
some text

```json
{"test":"value"}
```

more text
    """
    data = lib_naan.ghissue.extract_json_block_from_markdown(md)
    assert data["test"] == "value"

