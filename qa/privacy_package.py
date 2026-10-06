"""Reject identifying project material and runtime bootstrap in the release ZIP."""
import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from macro.session import VERSION

root=Path(__file__).resolve().parents[1]
archive=root/'dist/windows'/f'MouseMacroStocazzSuperpower-Windows-v{VERSION}.zip'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--deny-list',type=Path,required=True,help='Private JSON array of identifying strings; never commit this file.')
args=parser.parse_args()
private_terms=json.loads(args.deny_list.read_text('utf-8'))
if not isinstance(private_terms,list) or not private_terms or any(not isinstance(term,str) or not term.strip() for term in private_terms):
    parser.error('The private deny list must be a non-empty JSON array of strings.')
forbidden=tuple(term.lower() for term in private_terms)+('by codex','project-status.local','project-history.local')
with zipfile.ZipFile(archive) as z:
    for name in z.namelist():
        content=z.read(name)
        for term in forbidden:
            assert term not in name.lower(),name
            for encoding in ('utf-8','utf-16-le'):
                # A four-character byte sequence can occur by chance in signed
                # third-party machine code. Check short names in text/metadata,
                # and full identifiers in every file; preserve original binaries.
                if len(term)>=8:
                    assert term.encode(encoding) not in content.lower(),(name,term)
        if Path(name).suffix.lower() in ('.py','.md','.json','.txt','.html','.cs','.svg'):
            text=content.decode('utf-8',errors='replace').lower()
            for term in forbidden:
                assert not re.search(r'\b'+re.escape(term)+r'\b',text),(name,term)
        if Path(name).suffix.lower()=='.png':
            from PIL import Image
            metadata=json.dumps(Image.open(io.BytesIO(content)).info,default=str).lower()
            for term in forbidden:
                assert term not in metadata,(name,term)
        assert not name.endswith(('.pyc','.pdb')),name
        assert '/sitecustomize.py' not in name,name
portable=root/'dist/windows/MouseMacroStocazzSuperpower-Windows-Portable.zip'
assert hashlib.sha256(portable.read_bytes()).digest()==hashlib.sha256(archive.read_bytes()).digest()
print('PACKAGE_PRIVACY_OK; PORTABLE_ALIAS_IDENTICAL')
