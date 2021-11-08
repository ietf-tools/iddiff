# iddiff
Internet-Draft (ID) diff tool. Inspired by
[rfcdiff](https://tools.ietf.org/rfcdiff).

## Install

NOTE: Tested with Python 3.8.

```
pip install iddiff
```

## Usage
```
usage: iddiff.py [-h] [-t] [-c] [-l LINES] [--version] file1 file2

Internet-Draft diff tool

positional arguments:
  file1
  file2

optional arguments:
  -h, --help            show this help message and exit
  -t, --table           produce a HTML table (default)
  -c, --context         produce a context (default)
  -l LINES, --lines LINES
                        set number of context lines (default 8)
  --version             show program's version number and exit
```
