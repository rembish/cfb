# cfb

Read-only access to Microsoft Compound File Binary (CFB/OLE2) files from Python.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Or use the Makefile:

```bash
make install
```

## Usage

```python
from cfb import CfbIO
from cfb.directory.entry import SEEK_END

doc = CfbIO("tests/data/simple.doc")

# Read the root entry buffer.
root = doc.root
print(root.read())

# Access entries by name and seek within them.
entry = doc["1Table"]
entry.seek(100, SEEK_END)
print(entry.read(100))

# Access entries by directory ID.
sibling = doc[1].left
sibling.seek(0)
print(sibling.read(64))
```

All objects are lazy-loaded, so opening a large file only reads data when
you explicitly access it.

## Development

```bash
make install     # create .venv and install all dev dependencies
make format      # run black
make lint        # run ruff
make typecheck   # run mypy
make test        # run pytest with coverage
make clean       # remove build artefacts and the virtualenv
```

## License

BSD 2-Clause — see `LICENSE.txt`.
