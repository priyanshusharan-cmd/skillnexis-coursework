# Summary: Style Guide for Python Code

*Source:* https://raw.githubusercontent.com/python/peps/main/peps/pep-0008.rst  
*Length:* 5715 words · *Engine:* `offline:textrank (extractive: key points are the article's own most central sentences)`

**TL;DR:** In Python, this style is generally deemed unnecessary because attribute and method names are prefixed with an object, and function names are prefixed with a module name.

**Key points**

- In Python code, it is permissible to break before or after a binary operator, as long as the convention is consistent locally.
- Module level "dunders" such as __all__, __author__, __version__, etc. should be placed after the module docstring but before any import statements except from __future__ imports.
- Each line of a block comment starts with a # and a single space.
- In Python, this style is generally deemed unnecessary because attribute and method names are prefixed with an object, and function names are prefixed with a module name.
- Always decide whether a class's methods and instance variables should be public or non-public.

**Who should read it:** Anyone interested in names, line, code.
