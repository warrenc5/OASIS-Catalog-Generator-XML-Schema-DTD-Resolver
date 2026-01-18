#!/usr/bin/python3
import os
import sys
import re
import argparse
import xml.etree.ElementTree as etree
#from lxml import etree

def get_schema_namespace(xsd_file):
    tree = etree.parse(xsd_file)
    root = tree.getroot()
    # Namespace is usually in xmlns or xmlns:xs or similar
    ns_attr = [k for k in root.attrib if k.startswith('xmlns')]
    for attr in ns_attr:
        # We want the default xmlns or xmlns:* bound to xs
        # Try to find 'xmlns' or xmlns:xs or xmlns:xsd
        if attr == 'xmlns' or attr.startswith('xmlns:x'):
            return root.attrib[attr]
    # fallback: try 'targetNamespace' attribute if present
    return root.attrib.get('targetNamespace', None)

def extract_dtd_doctype(dtd_file):
    """Extract PUBLIC and SYSTEM identifiers from DOCTYPE declaration in DTD file."""
    with open(dtd_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Match multiline DOCTYPE declaration
    # Pattern: <!DOCTYPE ... PUBLIC "public_id" "system_id">
    pattern = r'<!DOCTYPE\s+\S+\s+PUBLIC\s+"([^"]+)"\s+"([^"]+)">'
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        public_id = match.group(1)
        system_id = match.group(2)
        return public_id, system_id
    return None, None

def find_common_prefix(namespaces):
    """Find the longest common prefix among a list of namespace strings."""
    if not namespaces:
        return ""
    if len(namespaces) == 1:
        return namespaces[0]

    # Sort to make comparison easier
    sorted_ns = sorted(namespaces)
    first = sorted_ns[0]
    last = sorted_ns[-1]

    # Find common prefix between first and last (which will be common to all)
    common = []
    for i in range(min(len(first), len(last))):
        if first[i] == last[i]:
            common.append(first[i])
        else:
            break

    return ''.join(common)

def main(directory, catalog_path, prefer_public=False):
    xsd_files = []
    dtd_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            full_path = os.path.abspath(os.path.join(dirpath, f))
            if f.endswith('.xsd'):
                xsd_files.append(full_path)
            elif f.endswith('.dtd'):
                dtd_files.append(full_path)

    catalog_entries = []
    namespaces = []
    system_ids = []

    # Process XSD files
    for xsd_file in xsd_files:
        schema_ns = get_schema_namespace(xsd_file)
        if not schema_ns:
            print(f"Warning: No schema namespace in {xsd_file}")
            continue
        rel_path = os.path.relpath(xsd_file, directory)
        # Create a <public> entry
        catalog_entries.append(
            f'    <public publicId="{schema_ns}" uri="{rel_path}"/>'
        )
        # Collect namespaces for finding common prefix
        namespaces.append(schema_ns)

    # Process DTD files
    for dtd_file in dtd_files:
        public_id, system_id = extract_dtd_doctype(dtd_file)
        if not public_id or not system_id:
            print(f"Warning: No DOCTYPE declaration found in {dtd_file}")
            continue
        rel_path = os.path.relpath(dtd_file, directory)
        # Create a <public> entry for PUBLIC identifier
        catalog_entries.append(
            f'    <public publicId="{public_id}" uri="{rel_path}"/>'
        )
        # Create a <system> entry for SYSTEM identifier
        catalog_entries.append(
            f'    <system systemId="{system_id}" uri="{rel_path}"/>'
        )
        # Collect system IDs for finding common prefix
        system_ids.append(system_id)

    # Find the longest common prefix for rewrite entries
    common_prefix = find_common_prefix(namespaces)
    common_system_prefix = find_common_prefix(system_ids)

    catalog = []
    catalog.append('<?xml version="1.0" encoding="UTF-8"?>')

    # Build catalog element with optional preferPublic attribute
    if prefer_public:
        catalog.append('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog" prefer="public">')
    else:
        catalog.append('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">')

    catalog.extend(catalog_entries)

    # Add rewrite entries for common prefixes
    rewrite_prefix = os.path.abspath(directory)
    if common_prefix:
        catalog.append(
            f'    <rewriteURI uriStartString="{common_prefix}" rewritePrefix="{rewrite_prefix}/"/>'
        )
    if common_system_prefix:
        catalog.append(
            f'    <rewriteSystem systemIdStartString="{common_system_prefix}" rewritePrefix="{rewrite_prefix}/"/>'
        )

    catalog.append('</catalog>')

    with open(catalog_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(catalog))

    print(f"Catalog written to {catalog_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Generate OASIS XML Catalog from XSD and DTD files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s test/schema galleon
  %(prog)s test/dtd slee --prefer-public
        '''
    )
    parser.add_argument('directory',
                        help='Directory containing XSD or DTD files')
    parser.add_argument('catalog_prefix',
                        help='Prefix for output catalog file (creates <prefix>-catalog.xml)')
    parser.add_argument('--prefer-public',
                        action='store_true',
                        help='Set prefer="public" attribute on catalog element (prefer PUBLIC identifiers over SYSTEM)')

    args = parser.parse_args()

    catalog_path = f"{args.catalog_prefix}-catalog.xml"
    main(args.directory, catalog_path, args.prefer_public)
