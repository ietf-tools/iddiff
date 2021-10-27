from argparse import ArgumentParser
from difflib import _mdiff as mdiff
from re import compile
from sys import stdout

SKIPS = [
    compile(r'^.*\[?[Pp]age [0-9ivx]+\]?[ \t\f]*$'),
    compile(r'^ *Internet.Draft.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *INTERNET.DRAFT.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *Draft.+(  +)[12][0-9][0-9][0-9] *$'),
    compile(r'^RFC[ -]?[0-9]+.*(  +).* [12][0-9][0-9][0-9]$'),
    compile(r'^draft-[-a-z0-9_.]+.*[0-9][0-9][0-9][0-9]$')]

HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title></title>
    <style>
      body {{font-family: monospace}}
      td {{
        white-space: pre;
        vertical-align: top;
        font-size: 0.86em;
      }}
      .left {{ background-color: #EEE; }}
      .right {{ background-color: #FFF; }}
      .lblock {{ background-color: #BFB; }}
      .rblock {{ background-color: #FF8; }}
      .delete {{ background-color: #ACF; }}
      .insert {{ background-color: #8FF; }}
    </style>
  </head>
  <body>
    <table>
     {rows}
    </table>
  </body>
</html>"""

UNCHANGED_ROW = """
      <tr>
        <td>&nbsp;</td>
        <td class="left">{lline}</td>
        <td>&nbsp;</td>
        <td class="right">{rline}</td>
      </tr>"""

CHANGED_ROW = """
      <tr>
        <td>&nbsp;</td>
        <td class="lblock">{lline}</td>
        <td>&nbsp;</td>
        <td class="rblock">{rline}</td>
      </tr>"""


def cleanup(lines):
    id_lines = []
    for line in lines:
        if len(line.strip()) > 0:
            keep = True
            for skip in SKIPS:
                if skip.match(line):
                    keep = False
                    break
            if keep:
                id_lines.append(line)
    return id_lines


def add_span(line, css_class):
    return line.replace('\0+', '<span class="{}">'.format(css_class)). \
                replace('\0-', '<span class="{}">'.format(css_class)). \
                replace('\0^', '<span class="{}">'.format(css_class)). \
                replace('\1', '</span>')


def main():
    parser = ArgumentParser(description='ID Diff')
    parser.add_argument('file1')
    parser.add_argument('file2')
    options = parser.parse_args()

    file1 = options.file1
    file2 = options.file2
    with open(file1, 'r') as file:
        id_a_lines = cleanup(file.readlines())
    with open(file2, 'r') as file:
        id_b_lines = cleanup(file.readlines())

    rows = ''
    diffs = mdiff(id_a_lines, id_b_lines)
    for lb, rb, different in diffs:
        if not different:
            rows += UNCHANGED_ROW.format(lline=lb[1], rline=rb[1])
        else:
            lline = add_span(lb[1], 'delete')
            rline = add_span(rb[1], 'insert')
            rows += CHANGED_ROW.format(lline=lline, rline=rline)
    rows.replace('\t', '&nbsp;')
    stdout.writelines(HTML.format(rows=rows))


if __name__ == '__main__':
    main()
