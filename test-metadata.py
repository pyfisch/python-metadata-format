#!/usr/bin/env python3
"""
Parse all METADATA/WHEEL/PKG-INFO files found in a given directory
and print errors.

Usage: ./test-metadata.py [folder]
"""

import os
import sys
import logging

import metadata


logger = logging.getLogger(__name__)


def test_file(root, file):
    fp = open(root + "/" + file)
    # Parse file.
    if file == "PKG-INFO":
        meta = metadata.PkgInfo.parse(fp)
    elif file == "METADATA":
        meta = metadata.Metadata.parse(fp)
    elif file == "WHEEL":
        meta = metadata.Wheel.parse(fp)
    else:
        return
    # Write file to string.
    _ = str(meta)


def main():
    logging.basicConfig(level=logging.WARNING)
    path = sys.argv[1]
    for root, _dirs, files in os.walk(path):
        for file in files:
            try:
                test_file(root, file)
            except Exception as e:
                logging.error(f"Parsing {root}/{file} failed.", exc_info=e)


if __name__ == "__main__":
    main()
