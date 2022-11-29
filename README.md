# iddiff
Internet-Draft (ID) diff tool. Inspired by
[rfcdiff](https://tools.ietf.org/rfcdiff).

## Install

```
pip install iddiff
```

## Dependencies

* Python 3.8 or higher.
* Word difference functionality (`wdiff` and `hwdiff`) requires [GNU Wdiff](https://www.gnu.org/software/wdiff/).

## Usage
```
usage: iddiff [-h] [--side-by-side | --wdiff | --hwdiff | --chbars | --abdiff]
              [-t] [-c CONTEXT_LINES] [-s] [-v]
              file1 file2

Internet-Draft diff tool

positional arguments:
  file1                 first file to compare
  file2                 second file to compare

options:
  -h, --help            show this help message and exit
  --side-by-side        side by side difference (default)
  --wdiff               produce word difference (requries GNU Wdiff)
  --hwdiff              produce HTML wrapped word difference
                        (requires GNU Wdiff)
  --chbars              produce changebar marked output
  --abdiff              produce before/after output
  -s, --skip-whitespace
                        skip multilines with only whitespace
  -v, --version         show program's version number and exit

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
