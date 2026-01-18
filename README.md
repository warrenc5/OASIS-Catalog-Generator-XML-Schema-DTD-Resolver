# OASIS Catalog Generator for XML Schemas and DTDs

A Python utility that automatically generates OASIS XML Catalogs from directories containing XML Schema Definition (XSD) files and Document Type Definition (DTD) files.

## What Problem Does This Solve?

When working with XML files, applications often need to validate them against schemas or DTDs. These schemas are typically referenced by URLs like `http://java.sun.com/dtd/slee-sbb-jar_1_0.dtd`. However, fetching these resources from the internet every time can be:

- **Slow**: Network requests add latency
- **Unreliable**: URLs may be unavailable or deprecated
- **Inefficient**: The same schema gets downloaded repeatedly

**OASIS XML Catalogs** solve this by mapping remote URLs to local files, allowing XML parsers to use local copies instead of fetching from the internet.

## What is an OASIS Catalog?

An OASIS XML Catalog is a standardized format (defined by [OASIS Standard V1.1](https://www.oasis-open.org/committees/entity/spec-2001-08-06.html)) that maps:
- **PUBLIC identifiers** (formal public identifiers like `-//Sun Microsystems, Inc.//DTD JAIN SLEE SBB 1.0//EN`)
- **SYSTEM identifiers** (URLs like `http://java.sun.com/dtd/slee-sbb-jar_1_0.dtd`)
- **Namespace URIs** (like `urn:jboss:galleon:package:2.0`)

...to local file paths on your system.

XML parsers that support catalogs (most do) will automatically use your local files instead of making network requests.

## How It Works

The `catgen.py` utility:

1. **Scans a directory** for `.xsd` and `.dtd` files
2. **Extracts identifiers**:
   - For XSD files: Reads the XML namespace from the schema
   - For DTD files: Parses the DOCTYPE declaration embedded in comments
3. **Generates catalog entries** mapping those identifiers to local file paths
4. **Creates rewrite rules** using the longest common prefix to handle related schemas efficiently

## Usage

```bash
python3 catgen.py <directory> <catalog-prefix>
```

### Parameters

- `<directory>`: Path to the directory containing your XSD or DTD files
- `<catalog-prefix>`: Name prefix for the output catalog (will create `<prefix>-catalog.xml`)

### Examples

From the included test cases:

```bash
# Generate a catalog for Galleon XML schemas
python3 catgen.py test/schema galleon-test
# Creates: galleon-test-catalog.xml

# Generate a catalog for JAIN SLEE DTD files
python3 catgen.py test/dtd slee-test
# Creates: slee-test-catalog.xml
```

You can run both examples using:
```bash
./test.sh
```

## Sample Output

### For XML Schemas (galleon-test-catalog.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
    <public publicId="urn:jboss:galleon:package:2.0" uri="galleon-package-2_0.xsd"/>
    <public publicId="urn:jboss:galleon:provisioning:4.0" uri="galleon-provisioning-4_0.xsd"/>
    <public publicId="urn:jboss:galleon:layer-spec:1.0" uri="galleon-layer-1_0.xsd"/>
    <!-- ... more entries ... -->
    <rewriteURI uriStartString="urn:jboss:galleon:" 
                rewritePrefix="/path/to/test/schema/"/>
</catalog>
```

**What this does:**
- Each `<public>` entry maps a namespace URI to a local XSD file
- The `<rewriteURI>` rule catches any URI starting with `urn:jboss:galleon:` and redirects it to your local directory

### For DTD Files (slee-test-catalog.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog">
    <public publicId="-//Sun Microsystems, Inc.//DTD JAIN SLEE SBB 1.0//EN" 
            uri="slee-sbb-jar_1_0.dtd"/>
    <system systemId="http://java.sun.com/dtd/slee-sbb-jar_1_0.dtd" 
            uri="slee-sbb-jar_1_0.dtd"/>
    <!-- ... more entries ... -->
    <rewriteSystem systemIdStartString="http://java.sun.com/dtd/slee-" 
                   rewritePrefix="/path/to/test/dtd/"/>
</catalog>
```

**What this does:**
- Each `<public>` entry maps a formal PUBLIC identifier to a local DTD file
- Each `<system>` entry maps a SYSTEM identifier (URL) to a local DTD file
- The `<rewriteSystem>` rule catches any URL starting with `http://java.sun.com/dtd/slee-` and redirects it to your local directory

## Important Limitation: DTD Files and PUBLIC Identifiers

### The Challenge

DTD files themselves **do not contain their own PUBLIC identifiers**. Unlike XML Schema files which declare their namespace internally, DTD files are just grammar definitions with no self-describing metadata.

The PUBLIC identifier is only known by the XML documents that reference the DTD, typically in their DOCTYPE declarations:

```xml
<!DOCTYPE sbb-jar PUBLIC
    "-//Sun Microsystems, Inc.//DTD JAIN SLEE SBB 1.0//EN"
    "http://java.sun.com/dtd/slee-sbb-jar_1_0.dtd">
```

### Our Solution

This utility works around this limitation by looking for **example DOCTYPE declarations in comments** within the DTD files themselves. Many well-documented DTD files (like the JAIN SLEE DTDs) include example DOCTYPE declarations in their header comments showing developers how to use them:

```dtd
<!--
This is the XML DTD for the JAIN SLEE 1.0 sbb component jar file deployment
descriptor. All JAIN SLEE 1.0 sbb component jar file deployment descriptors
must include a DOCTYPE of the following form:

  <!DOCTYPE sbb-jar PUBLIC
        "-//Sun Microsystems, Inc.//DTD JAIN SLEE SBB 1.0//EN"
        "http://java.sun.com/dtd/slee-sbb-jar_1_0.dtd">
-->
```

The utility extracts these PUBLIC and SYSTEM identifiers from the comments.

### When This Doesn't Work

If a DTD file doesn't include an example DOCTYPE declaration in its comments, the utility will:
- Print a warning: `Warning: No DOCTYPE declaration found in <filename>`
- Skip that file and continue processing others

**Workaround:** You can manually add the catalog entries if you know the PUBLIC identifier from the XML documents that use the DTD.

## Technical References

- [OASIS XML Catalogs V1.1 Specification](https://www.oasis-open.org/committees/entity/spec-2001-08-06.html)
- [W3C XML Schema Specification](https://www.w3.org/XML/Schema)
- [W3C XML 1.0 Specification (DTD Definition)](https://www.w3.org/TR/xml/)

## Requirements

- Python 3.x
- Standard library only (no external dependencies)

## Using Generated Catalogs

To use the generated catalog with XML parsers:

**Java (with Apache XML Commons Resolver):**
```java
System.setProperty("xml.catalog.files", "path/to/catalog.xml");
```

**Python (with lxml):**
```python
from lxml import etree
catalog = etree.XMLCatalog(file="path/to/catalog.xml")
parser = etree.XMLParser(catalog=catalog)
```

**XML Editor (e.g., Oxygen, IntelliJ IDEA):**
Most XML editors support OASIS catalogs through their preferences/settings. Point them to your generated catalog file.

## License

See LICENSE file for details.
