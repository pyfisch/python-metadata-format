Python Metadata Format
======================

The Python Metadata Format is used for the `METADATA` and `WHEEL` files in wheels and `PKG-INFO` files sdists.
It consists of an ordered list of key-value pairs and an optional multi-line payload.

Currently (March 2021) the format is specified by [PEP 241] as a "a single set of RFC-822 headers parseable by the rfc822.py module."
However the original  [RFC 822] was written in 1982 and is obsoleted and significantly extended by subsequent RFCs.
While the `rfc822.py` module was removed in Python 3,
these messages can be generated and parsed by the `email` package in the standard library,
but the choice of format parameters is left to implementations.
This situation has resulted in some confusion which metadata files are legal and what the recommended representation is.
Some metadata generators such as setuptools[1] and flit[2] have chosen to use string formatting for generating `PKG-INFO` and `METADATA` files instead of using a structured generator.
This has resulted in some malformed metadata. [3][4]

I'd like to propose a new specification of the Python Metadata Format,
that is independent from the email message syntax and backwards compatible with deployed metadata files.

File syntax
--------------

The file syntax is shared between `METADATA`, `WHEEL` and `PKG-INFO` files.
All files are UTF-8 encoded and line endings may be written as either `\r`, `\n` or `\r\n` (universal newlines).

Key-value pairs are written as "Key: Value", terminated by a newline.

Keys are case-insensitive, they consist of ASCII words separated by dashes (Regular expression: `[a-zA-Z]+(-[a-zA-Z]+)*`).
TODO: Be less strict? [RFC 5322] allows all printable ASCII characters except `:`.

Values are printable Unicode strings without line breaks. They may not contain ASCII control characters except for whitespace (Regular expression: `[^\x00-\x08\x0a-\x1f]*`, everything except ASCII control characters but including horizontal tab). Whitespace is stripped at the start and end of values.

For compatibility with existing metadata files a line-folding algorithm is specified.
Some values are stretched across multiple lines:

```
Author: C. Schultz, Universal Features Syndicate,
        Los Angeles, CA <cschultz@peanuts.example.com>
Description: This project provides powerful math functions
        |For example, you can use `sum()` to sum numbers:
        |
        |Example::
        |
        |    >>> sum(1, 2)
        |    3
        |
License: GPL
```

After reading a `Key: value` line, read all subsequent lines starting with a space character.
To reconstruct the original value replace the newlines and every whitespace following it with a single space character.
If the field name is `Description` and you are in a `METADATA` or `WHEEL` file use a different algorithm:

1. If a line starts with 7 spaces followed by a pipe (“|”) char, replace them with a newline. (common in older `METADATA` files)
2. If a line starts with 8 spaces, replace them with a newline. (common in `PKG-INFO` files)
3. Otherwise use a single space char like in other fields.

The list of key value pairs is terminated by two newlines.
The rest of the file is an optional multi-line payload which is used for descriptions in `METADATA` and `PKG-INFO` files.

[PEP 241]: https://www.python.org/dev/peps/pep-0241/
[RFC 822]: https://tools.ietf.org/html/rfc822
[RFC 5322]: https://tools.ietf.org/html/rfc5322#section-3.6.8
[1]: https://github.com/pypa/setuptools/blob/729c45d50afe7275ade53dd819d0e45547e98f01/setuptools/dist.py#L131-L200
[2]: https://github.com/takluyver/flit/blob/8f93601d05abe00c833663df541200114dbf3ad1/flit_core/flit_core/sdist.py
[3]: https://github.com/takluyver/flit/issues/387
[4]: https://github.com/pypa/setuptools/issues/1390
