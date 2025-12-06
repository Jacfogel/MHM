# Unconverted Links Test Fixture

This fixture tests unconverted HTML link detection.

## Valid Markdown Links

This section has properly formatted markdown links:
- [Valid markdown link](demo_module.py)
- [Another valid link](demo_module2.py)

## Unconverted HTML Links

This section has unconverted HTML-style links that should be detected:
- <a href="test.html">Old HTML link</a>
- <a href="another.html">Another old link</a>
- <a href="core/module.py">HTML link to Python file</a>

## Mixed Links

This section has both markdown and HTML links:
- [Markdown link](demo_module.py) - Should be valid
- <a href="old.html">HTML link</a> - Should be detected as unconverted

