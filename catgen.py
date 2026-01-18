#!/usr/bin/python3
import os
import sys
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

def main(directory, catalog_path):
    xsd_files = []
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.xsd'):
                xsd_files.append(os.path.abspath(os.path.join(dirpath, f)))

    catalog_entries = []
    rewrite_entries = set()

    for xsd_file in xsd_files:
        schema_ns = get_schema_namespace(xsd_file)
        if not schema_ns:
            print(f"Warning: No schema namespace in {xsd_file}")
            continue
        rel_path = os.path.relpath(xsd_file, directory)
        abs_path = os.path.abspath(xsd_file)
        # Create a <public> entry
        catalog_entries.append(
            f'    <public publicId="{schema_ns}" uri="{rel_path}"/>'
        )
        # Collect rewrite entries (one per namespace)
        rewrite_entries.add((schema_ns, abs_path))

    catalog = []
    catalog.append('<?xml version="1.0" encoding="UTF-8"?>')
    catalog.append('<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">')
    catalog.extend(catalog_entries)
    for ns, abs_path in rewrite_entries:
        # OASIS Catalog supports <rewriteURI uriStartString="..." rewritePrefix="..."/>
        catalog.append(
            f'    <rewriteURI uriStartString="{ns}" rewritePrefix="{abs_path}"/>'
        )
    catalog.append('</catalog>')

    with open(catalog_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(catalog))

    print(f"Catalog written to {catalog_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <xsd_directory> <catalog.xml>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

