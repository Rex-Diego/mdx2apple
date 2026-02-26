#!/usr/bin/env python3
"""
Convert MDict (.mdx) to macOS Dictionary format.

macOS Dictionary uses Apple Dictionary Development Kit format:
- Dictionary.xml (main content)
- DictInfo.plist (metadata)
- Then compile with Dictionary Development Kit
"""

import os
import re
import html
from pathlib import Path
from readmdict import MDX

def clean_html(content: str) -> str:
    """Clean and normalize HTML content for macOS Dictionary."""
    # Remove MDict-specific tags
    content = re.sub(r'<link[^>]*>', '', content)
    content = re.sub(r'@@@LINK=([^<\n]+)', r'<a href="x-dictionary:r:\1">\1</a>', content)
    return content

def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    return html.escape(text, quote=True)

def convert_mdx_to_apple_dict(mdx_path: str, output_dir: str = "AppleDict"):
    """Convert MDX file to Apple Dictionary XML format."""

    print(f"Reading {mdx_path}...")
    mdx = MDX(mdx_path)

    # Get all entries
    items = mdx.items()
    entries = [(key.decode('utf-8') if isinstance(key, bytes) else key,
                val.decode('utf-8') if isinstance(val, bytes) else val)
               for key, val in items]

    print(f"Found {len(entries)} entries")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Write Dictionary.xml
    xml_path = Path(output_dir) / "Dictionary.xml"
    print(f"Writing {xml_path}...")

    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<d:dictionary xmlns="http://www.w3.org/1999/xhtml" ')
        f.write('xmlns:d="http://www.apple.com/DTDs/DictionaryService-1.0.rng">\n\n')

        for i, (word, definition) in enumerate(entries):
            if not word or not definition:
                continue

            # Create entry ID (sanitized)
            entry_id = re.sub(r'[^a-zA-Z0-9_-]', '_', word)[:50]
            entry_id = f"entry_{i}_{entry_id}"

            # Clean definition HTML
            clean_def = clean_html(definition)

            f.write(f'<d:entry id="{entry_id}" d:title="{escape_xml(word)}">\n')
            f.write(f'  <d:index d:value="{escape_xml(word)}"/>\n')

            # Add lowercase index if different
            if word.lower() != word:
                f.write(f'  <d:index d:value="{escape_xml(word.lower())}"/>\n')

            f.write(f'  <h1>{escape_xml(word)}</h1>\n')
            f.write(f'  <div class="definition">{clean_def}</div>\n')
            f.write('</d:entry>\n\n')

            if (i + 1) % 5000 == 0:
                print(f"  Processed {i + 1} entries...")

        f.write('</d:dictionary>\n')

    # Write DictInfo.plist
    plist_path = Path(output_dir) / "DictInfo.plist"
    print(f"Writing {plist_path}...")

    with open(plist_path, 'w', encoding='utf-8') as f:
        f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleIdentifier</key>
    <string>com.etymonline.dictionary</string>
    <key>CFBundleName</key>
    <string>Etymonline</string>
    <key>CFBundleDisplayName</key>
    <string>Online Etymology Dictionary</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>DCSDictionaryCopyright</key>
    <string>etymonline.com</string>
    <key>DCSDictionaryManufacturerName</key>
    <string>Douglas Harper</string>
    <key>DCSDictionaryFrontMatterReferenceID</key>
    <string>front_matter</string>
</dict>
</plist>
''')

    # Write Makefile
    makefile_path = Path(output_dir) / "Makefile"
    print(f"Writing {makefile_path}...")

    with open(makefile_path, 'w', encoding='utf-8') as f:
        f.write('''# Makefile for Apple Dictionary
#
# Requirements:
# 1. Install Dictionary Development Kit from:
#    https://developer.apple.com/download/more/ (search "Auxiliary Tools")
# 2. Set DICT_BUILD_TOOL_DIR to the kit location

DICT_NAME = Etymonline
DICT_BUILD_TOOL_DIR = /Applications/Utilities/Dictionary\\ Development\\ Kit
DICT_BUILD_TOOL_BIN = $(DICT_BUILD_TOOL_DIR)/bin

# Build dictionary
build:
\t$(DICT_BUILD_TOOL_BIN)/build_dict.sh $(DICT_NAME) Dictionary.xml DictInfo.plist

# Install to user dictionary folder
install: build
\tmkdir -p ~/Library/Dictionaries
\tcp -R objects/$(DICT_NAME).dictionary ~/Library/Dictionaries/
\t@echo "Dictionary installed. Restart Dictionary.app to use."

# Clean build artifacts
clean:
\trm -rf objects

.PHONY: build install clean
''')

    # Write CSS
    css_path = Path(output_dir) / "Dictionary.css"
    print(f"Writing {css_path}...")

    # Copy original CSS if exists
    orig_css = Path(mdx_path).with_suffix('.css')
    if orig_css.exists():
        with open(orig_css, 'r', encoding='utf-8') as src:
            css_content = src.read()
    else:
        css_content = '''
/* Default styles for Etymonline dictionary */
h1 { font-size: 1.2em; font-weight: bold; color: #333; }
.definition { margin: 10px 0; line-height: 1.5; }
a { color: #0066cc; text-decoration: none; }
a:hover { text-decoration: underline; }
'''

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css_content)

    print(f"\nConversion complete!")
    print(f"\nNext steps:")
    print(f"1. Download Dictionary Development Kit from Apple Developer")
    print(f"2. cd {output_dir}")
    print(f"3. make build")
    print(f"4. make install")

if __name__ == "__main__":
    mdx_file = "ETYMONLINE.mdx"
    if os.path.exists(mdx_file):
        convert_mdx_to_apple_dict(mdx_file)
    else:
        print(f"Error: {mdx_file} not found")
