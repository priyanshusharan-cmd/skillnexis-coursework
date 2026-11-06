# Reading a Python error message (traceback)
Read errors from the bottom up. The last line tells you the error type and message, for example `NameError: name 'totl' is not defined`. The line above it shows the code that failed, and above that the file name and line number.

Common errors:
- **NameError**: a variable name is misspelt or used before it is created. Python often suggests "Did you mean...".
- **SyntaxError: invalid syntax**: a missing colon, bracket or quote, usually on the line shown or the line before.
- **IndentationError**: the lines inside an if, for or def must be indented by 4 spaces.
- **TypeError: can only concatenate str (not "int") to str**: you joined text and a number with +. Use `print("Total:", total)` or `str(total)`.

Watch the 3-minute video "How to Read a Python Error Message" for three worked examples.
