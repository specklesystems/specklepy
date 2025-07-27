# Third-Party Licenses

This directory contains license files for third-party dependencies used by specklepy.

## IfcOpenShell

IfcOpenShell is an optional dependency available through the `speckleifc` extra:

```bash
pip install specklepy[speckleifc]
```

IfcOpenShell is dual-licensed under:

- **LGPL-3.0** (`IfcOpenShell-LGPL-3.0.txt`) - GNU Lesser General Public License v3.0
- **GPL-3.0** (`IfcOpenShell-GPL-3.0.txt`) - GNU General Public License v3.0

### About IfcOpenShell

IfcOpenShell is an open source software library for working with Industry Foundation Classes (IFC). It provides complete parsing support for IFC2x3 TC1, IFC4 Add2 TC1, IFC4x1, IFC4x2, and IFC4x3 Add2.

- **Project**: https://github.com/IfcOpenShell/IfcOpenShell
- **Documentation**: https://docs.ifcopenshell.org/
- **License**: LGPL-3.0-or-later, GPL-3.0-or-later

When using specklepy with IfcOpenShell, you must comply with the terms of these licenses.

## License Compatibility

specklepy is licensed under Apache-2.0, which is compatible with LGPL-3.0 for dynamic linking scenarios (which is how IfcOpenShell is used as an optional dependency).
