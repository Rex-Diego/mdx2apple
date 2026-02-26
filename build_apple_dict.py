#!/usr/bin/env python3
"""
Build Apple Dictionary without Dictionary Development Kit.
Uses the open-source approach to create a working .dictionary bundle.
"""

import os
import re
import zlib
import struct
import hashlib
from pathlib import Path
from lxml import etree

def build_dictionary(source_dir: str, output_dir: str = None):
    """Build Apple Dictionary from source files."""

    source_path = Path(source_dir)
    xml_file = list(source_path.glob("*.xml"))[0]
    css_file = list(source_path.glob("*.css"))[0]
    plist_file = list(source_path.glob("*.plist"))[0]

    dict_name = xml_file.stem
    if output_dir is None:
        output_dir = Path.home() / "Library/Dictionaries" / f"{dict_name}.dictionary"
    else:
        output_dir = Path(output_dir)

    # Create bundle structure
    contents_dir = output_dir / "Contents"
    resources_dir = contents_dir / "Resources"
    body_dir = resources_dir / "Body.data"

    for d in [contents_dir, resources_dir, body_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {xml_file}...")

    # Parse XML and extract entries
    tree = etree.parse(str(xml_file))
    root = tree.getroot()

    # Handle namespace
    ns = {'d': 'http://www.apple.com/DTDs/DictionaryService-1.0.rng'}
    entries = root.findall('.//d:entry', ns)

    print(f"Found {len(entries)} entries")

    # Build key-text index
    key_text_data = []
    entry_data = []

    for i, entry in enumerate(entries):
        entry_id = entry.get('id', f'entry_{i}')
        title = entry.get('{http://www.apple.com/DTDs/DictionaryService-1.0.rng}title', '')

        # Get all index values
        indexes = entry.findall('.//d:index', ns)
        keys = [idx.get('{http://www.apple.com/DTDs/DictionaryService-1.0.rng}value', '') for idx in indexes]
        if not keys and title:
            keys = [title]

        # Get entry HTML content
        entry_html = etree.tostring(entry, encoding='unicode', method='html')

        for key in keys:
            if key:
                key_text_data.append((key.lower(), entry_id, entry_html))

        if (i + 1) % 5000 == 0:
            print(f"  Processed {i + 1} entries...")

    # Sort by key
    key_text_data.sort(key=lambda x: x[0])

    print("Building index...")

    # Create KeyText.index (simplified format)
    # Apple's format is complex, we'll create a basic searchable structure

    # Write DefaultStyle.css
    with open(css_file, 'r', encoding='utf-8') as f:
        css_content = f.read()
    with open(resources_dir / "DefaultStyle.css", 'w', encoding='utf-8') as f:
        f.write(css_content)

    # Write Info.plist
    with open(plist_file, 'r', encoding='utf-8') as f:
        plist_content = f.read()

    # Modify plist for bundle
    plist_content = plist_content.replace('</dict>', '''
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>DICT</string>
</dict>''')

    with open(contents_dir / "Info.plist", 'w', encoding='utf-8') as f:
        f.write(plist_content)

    # Create a simple body data file
    # This is a simplified version - full Apple format is proprietary
    print("Writing body data...")

    body_content = []
    for key, entry_id, html in key_text_data:
        body_content.append(f"<!-- {key} -->\n{html}\n")

    body_text = "\n".join(body_content)

    # Compress body data
    compressed = zlib.compress(body_text.encode('utf-8'), 9)

    with open(body_dir / "body.data", 'wb') as f:
        f.write(compressed)

    # Write key index (simple text format for now)
    with open(resources_dir / "KeyText.index", 'w', encoding='utf-8') as f:
        for key, entry_id, _ in key_text_data:
            f.write(f"{key}\t{entry_id}\n")

    print(f"\nDictionary bundle created at: {output_dir}")
    print("\nNote: This is a simplified format. For full functionality,")
    print("you need Apple's Dictionary Development Kit to compile properly.")

    return output_dir

if __name__ == "__main__":
    import sys
    source = sys.argv[1] if len(sys.argv) > 1 else "Etymonline.dictionary"
    build_dictionary(source)
