"""Monarch runs from its source files (wizard.md `runtime.package: source`): the App Manager mounts this repo at
the pinned commit on /app, so nothing is inlined into the compose any more (the inlined start argument grew
toward Linux's 128 KiB limit for one argument; humanitylabs-org/wizard-monarch#2).

Run from the repo root:  python3 tools/package.py --check   (checks that the compose and wizard.md agree)"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
LIMIT = 4096  # bytes for any one compose line: the start command must stay small as the app grows


def check():
    import yaml
    meta = (root / 'wizard.md').read_text().split('---')[1]
    runtime = yaml.safe_load(meta)['runtime']
    assert runtime.get('package') == 'source', 'wizard.md runtime.package must be source'
    text = (root / 'runtipi/docker-compose.yml').read_text()
    assert 'b64decode' not in text, 'compose still inlines the source'
    longest = max(len(line.encode()) for line in text.splitlines())
    assert longest < LIMIT, f'compose line of {longest} bytes'
    svc = yaml.safe_load(text)['services']['wizard-monarch']
    assert svc['command'] == ['python', '/app/app/server.py'], svc['command']
    assert svc['working_dir'] == '/app'
    assert '${APP_SOURCE_DIR}:/app:ro' in svc['volumes'], svc['volumes']
    assert '${APP_DATA_DIR}/data:/data' in svc['volumes']
    assert svc['read_only'] is True and svc['user'] == '1000:1000' and svc['pids_limit'] == 64
    assert '@sha256:' in svc['image']
    assert svc['environment']['PORT'] == '8806' and svc['environment']['DATA_DIR'] == '/data/private'
    for rel in ('app/server.py', 'web/app.js', 'web/index.html', 'openapi.json'):
        assert (root / rel).is_file(), f'missing runtime file {rel}'
    print(f'PASS: runs from source (runtime.package: source); longest compose line {longest} bytes')


if __name__ == '__main__':
    if '--check' not in sys.argv:
        print('Nothing to package: Monarch runs from source (runtime.package: source). Checking instead.')
    check()
