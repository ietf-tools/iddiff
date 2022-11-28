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
usage: iddiff [-h] [--side-by-side | -w | -hw | --chbars | -ab]
              [-t] [-c CONTEXT_LINES] [-s] [--version]
              file1 file2

Internet-Draft diff tool

positional arguments:
  file1                 first file to compare
  file2                 second file to compare

optional arguments:
  -h, --help            show this help message and exit
  --side-by-side        side by side difference (default)
  -w, --wdiff           produce word difference (requries GNU Wdiff)
  -hw, --hwdiff         produce HTML wrapped word difference (requires GNU Wdiff)
  --chbars              produce changebar marked output
  -ab, --abdiff         produce before/after output
  -s, --skip-whitespace
                        skip multilines with only whitespace
  --version             show program's version number and exit

side by side options:
  -t, --table-only      produce only a HTML table
  -c CONTEXT_LINES, --context-lines CONTEXT_LINES
                        set number of context lines (set to 0 for no context)
                        (default 8)
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
