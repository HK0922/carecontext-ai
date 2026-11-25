"""Dataset manifest reader: no credential bypass, scraping, or automatic restricted downloads."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'data/registry.json'


def main():
    parser=argparse.ArgumentParser(description='Inspect clinical reference/dataset permissions and local fingerprints.')
    parser.add_argument('--validate',action='store_true')
    args=parser.parse_args()
    registry=json.loads(REGISTRY.read_text())
    for entry in registry['sources']:
        path = ROOT / entry['local_path'] if entry['local_path'] else None
        digest=hashlib.sha256(path.read_bytes()).hexdigest() if path is not None and path.is_file() else None
        if path and not path.is_file():raise SystemExit(f'Missing local registered file: {entry["id"]}')
        if args.validate and path and entry['checksum'] and digest != entry['checksum']:
            raise SystemExit(f'Fingerprint mismatch: {entry["id"]}')
        print(f'{entry["id"]:28} access={entry["access"]}\n  upstream={entry["url"] or "local"}\n  local_sha256={digest or "not acquired"}\n')
    if args.validate:print('Registry syntax and local existence checks passed. No restricted datasets downloaded.')

if __name__=='__main__': main()
