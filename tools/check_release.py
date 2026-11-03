"""Verify explicit working-tree and tracked-file boundaries; never upload."""

from pathlib import Path
import json
import re
import struct
import subprocess
import sys
import zlib
import xml.etree.ElementTree as ET


def check_preview(data):
    expected = {'Software': 'Synthetic Signal States',
                'Description': 'Independent invented continuous-function comparison.'}
    if not data.startswith(b'\x89PNG\r\n\x1a\n') or len(data) > 2_000_000:
        raise ValueError('Unsupported preview.')
    offset, metadata, kinds = 8, {}, []
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError('Truncated image.')
        size = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        stop = offset + 12 + size
        if stop > len(data) or kind not in {b'IHDR', b'IDAT', b'IEND', b'pHYs', b'tEXt'}:
            raise ValueError('Unexpected image metadata.')
        body = data[offset + 8:stop - 4]
        if zlib.crc32(kind + body) & 0xffffffff != struct.unpack('>I', data[stop - 4:stop])[0]:
            raise ValueError('Invalid image checksum.')
        if kind == b'IHDR' and (len(body) != 13 or struct.unpack('>II', body[:8]) != (1800, 1500)):
            raise ValueError('Unexpected image dimensions.')
        if kind == b'tEXt':
            key, separator, value = body.partition(b'\0')
            key, value = key.decode('latin1'), value.decode('latin1')
            if not separator or key in metadata or expected.get(key) != value:
                raise ValueError('Unexpected image text metadata.')
            metadata[key] = value
        kinds.append(kind)
        offset = stop
        if kind == b'IEND':
            if body or offset != len(data):
                raise ValueError('Trailing image data.')
            break
    if not kinds or kinds[0] != b'IHDR' or kinds[-1] != b'IEND' or kinds.count(b'IHDR') != 1 or b'IDAT' not in kinds or metadata != expected:
        raise ValueError('Incomplete image structure.')


def check_research_report(root):
    sys.path.insert(0, str(root))
    from signal_demo.research import invented_cases
    expected = {'schema_version': 1, 'synthetic_only': True,
                'difference_convention': 'phase minus amplitude',
                'cases': {name: case['metrics'] for name, case in invented_cases().items()}}
    actual = json.loads((root / 'docs/results/research-metrics.json').read_text(encoding='utf-8'))
    def normalized(value):
        if isinstance(value, float):
            return round(value, 12)
        if isinstance(value, list):
            return [normalized(item) for item in value]
        if isinstance(value, dict):
            return {key: normalized(item) for key, item in value.items()}
        return value
    if normalized(expected) != normalized(actual):
        raise ValueError('Research report differs from the invented generator.')


def check_sorting_report(root):
    sys.path.insert(0, str(root))
    from signal_demo.sorting import study_report
    from tools.generate_sorting_study import markdown
    expected = study_report()
    actual = json.loads((root / 'docs/results/sorting-study.json').read_text(encoding='utf-8'))

    def normalized(value):
        if isinstance(value, float):
            return round(value, 10)
        if isinstance(value, list):
            return [normalized(item) for item in value]
        if isinstance(value, dict):
            return {key: normalized(item) for key, item in value.items()}
        return value

    if normalized(actual) != normalized(expected):
        raise ValueError('Sorting report differs from the independent synthetic generator.')
    saved_markdown = (root / 'docs/SORTING_RESULTS.md').read_text(encoding='utf-8')
    if saved_markdown != markdown(expected):
        raise ValueError('Readable sorting results differ from the numeric report.')


def check_sorting_svg(data):
    """Allow only passive plotting elements and fixed nonidentifying metadata."""
    if len(data) > 1_000_000 or b'<!ENTITY' in data.upper():
        raise ValueError('Unsupported SVG structure.')
    root = ET.fromstring(data)
    svg = '{http://www.w3.org/2000/svg}'
    dc = '{http://purl.org/dc/elements/1.1/}'
    rdf = '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}'
    cc = '{http://creativecommons.org/ns#}'
    tags = {svg + name for name in ('svg', 'metadata', 'defs', 'style', 'g',
                                    'path', 'clipPath', 'use', 'rect')}
    tags.update({rdf + 'RDF', cc + 'Work', cc + 'Agent', dc + 'type',
                 dc + 'format', dc + 'creator', dc + 'title'})
    if root.tag != svg + 'svg' or root.get('viewBox') != '0 0 518.4 612':
        raise ValueError('Unexpected synthetic figure dimensions.')
    titles = [item.text for item in root.iter(dc + 'title')]
    formats = [item.text for item in root.iter(dc + 'format')]
    if titles != ['Breath State Laboratory synthetic study'] or formats != ['image/svg+xml']:
        raise ValueError('Unexpected synthetic figure metadata.')
    for item in root.iter():
        if item.tag not in tags:
            raise ValueError('Unsupported SVG element.')
        for key, value in item.attrib.items():
            local = key.rsplit('}', 1)[-1].lower()
            if local.startswith('on') or local in ('src', 'base'):
                raise ValueError('Active SVG attributes are not permitted.')
            if local == 'href' and not value.startswith('#'):
                raise ValueError('External SVG resources are not permitted.')
            if any(not match.group(1).strip().strip('\"\'').startswith('#')
                   for match in re.finditer(r'url\(([^)]*)\)', value, re.IGNORECASE)):
                raise ValueError('External SVG paint resources are not permitted.')
            if local == 'resource' and not (
                item.tag == dc + 'type' and value == 'http://purl.org/dc/dcmitype/StillImage'
            ):
                raise ValueError('Unexpected SVG resource metadata.')
        style = item.text if item.tag == svg + 'style' else item.get('style', '')
        if style and ('@import' in style.lower() or any(
            not match.group(1).strip().strip('\"\'').startswith('#')
            for match in re.finditer(r'url\(([^)]*)\)', style, re.IGNORECASE)
        )):
            raise ValueError('External SVG styling is not permitted.')


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    entries = (root / "PUBLICATION_ALLOWLIST.txt").read_text(encoding="utf-8").splitlines()
    allowed = set(entries)
    if len(allowed) != len(entries) or any(
        not item or "\\" in item or item.startswith("/") or ".." in Path(item).parts
        for item in entries
    ):
        print("FAIL: malformed or duplicate allowlist entry.")
        return 1
    command = ["git", "--no-optional-locks", "-c", "core.fsmonitor=false", "-C", str(root)]
    try:
        tracked = subprocess.run(command + ["ls-files", "-z"], check=True, capture_output=True).stdout
        others = subprocess.run(command + ["ls-files", "--others", "--exclude-standard", "-z"],
                                check=True, capture_output=True).stdout
    except (OSError, subprocess.CalledProcessError):
        print("FAIL: local Git inventory unavailable.")
        return 1
    tracked_names = {item.decode("utf-8") for item in tracked.split(b"\0") if item}
    other_names = {item.decode("utf-8") for item in others.split(b"\0") if item}
    if tracked_names != allowed or other_names - allowed:
        print("FAIL: tracked or non-ignored files differ from the publication allowlist.")
        return 1
    for entry in entries:
        path = root / entry
        if not path.is_file() or path.is_symlink() or any(
            (root / parent).is_symlink() for parent in path.relative_to(root).parents
            if parent != Path(".")
        ):
            print("FAIL: allowlisted entry is missing or is a symbolic link.")
            return 1
        try:
            if entry == 'docs/figures/breath-state-functions.png':
                check_preview(path.read_bytes())
            elif entry.startswith('docs/figures/') and entry.endswith('.svg'):
                check_sorting_svg(path.read_bytes())
            else:
                path.read_text(encoding="utf-8")
        except (UnicodeError, OSError, ValueError, ET.ParseError):
            print("FAIL: a release file or its metadata requires review.")
            return 1
    try:
        check_research_report(root)
        check_sorting_report(root)
    except (OSError, ValueError):
        print('FAIL: a synthetic numeric or readable report requires review.')
        return 1
    print(f"PASS: {len(allowed)} allowlisted files; PNG/SVG structure and both synthetic reports checked.")
    print("Manual content, staged-blob, history, and permission review is still required.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
