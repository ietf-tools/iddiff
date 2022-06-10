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
usage: iddiff [-h] [-t] [-c] [-l LINES] [-w] [-s] [--version] file1 file2

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
  -w, --wdiff           produce word difference
  -s, --skip-whitespaces
                        skip multilines with only whitespaces
  --version             show program's version number and exit
```

## Tests

Run tests with [tox](https://tox.wiki/).
```
tox
```

Generate coverage report with [coverage](https://github.com/nedbat/coveragepy).
```
coverage report
```
