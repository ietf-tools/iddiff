from argparse import ArgumentParser
from difflib import _mdiff as mdiff, SequenceMatcher
from html import escape
from re import compile
from string import whitespace
from sys import exit, stderr, stdout

VERSION = '0.2.0'

SKIPS = [
    compile(r'^.*\[?[Pp]age [0-9ivx]+\]?[ \t\f]*$'),
    compile(r'^ *Internet.Draft.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *INTERNET.DRAFT.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *Draft.+(  +)[12][0-9][0-9][0-9] *$'),
    compile(r'^RFC[ -]?[0-9]+.*(  +).* [12][0-9][0-9][0-9]$'),
    compile(r'^draft-[-a-z0-9_.]+.*[0-9][0-9][0-9][0-9]$')]

TABLE = """
    <table>
      <tbody>
        <tr>
          <td>&nbsp;</td>
          <th class="header" scope="col">{filename1}</th>
          <td>&nbsp;</td>
          <th class="header" scope="col">{filename2}</th>
        </tr>{rows}
      </tbody>
    </table>"""

HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
      body {{font-family: monospace}}
      table {{
        border-spacing: 0;
      }}
      td {{
        padding: 0;
        white-space: pre;
        vertical-align: top;
        font-size: 0.86em;
      }}
      th {{
        padding: 0;
        text-align: center;
      }}
      .left {{ background-color: #EEE; }}
      .right {{ background-color: #FFF; }}
      .lblock {{ background-color: #BFB; }}
      .rblock {{ background-color: #FF8; }}
      .delete {{ background-color: #ACF; }}
      .insert {{ background-color: #8FF; }}
      .change {{ background-color: gray; }}
      .header {{ background-color: orange; }}
      .w-delete {{
        color: #F00;
        text-decoration: line-through;
      }}
      .w-insert {{
        color: #008000;
        font-weight: bold;
      }}
    </style>
  </head>
  <body>{output}</body>
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

CONTEXT_LINE = """
      <tr>
        <td>&nbsp;</td>
        <td class="left">&nbsp;</td>
        <td>&nbsp;</td>
        <td class="right">&nbsp;</td>
      </tr>
      <tr id="context-{context}">
        <td></td>
        <th class="change" scope="col">
          <a href="#context-{context}">
           <small>Skipping</small>
          </a>
        </th>
        <td></td>
        <th class="change" scope="col">
          <a href="#context-{context}">
           <small>Skipping</small>
          </a>
        </th>
      </tr>"""

WHITESPACE = ''.join([
    whitespace,  # python stirng.whitespace
    '\u0009',    # character tabulation
    '\u000A',    # line feed
    '\u000B',    # line tabulation
    '\u000C',    # form feed
    '\u000D',    # carriage return
    '\u0020',    # space
    '\u0085',    # next line
    '\u00A0',    # no-break space
    '\u1680',    # ogham space mark
    '\u2000',    # en quad
    '\u2001',    # em quad
    '\u2002',    # en space
    '\u2003',    # em space
    '\u2004',    # three-per-em space
    '\u2005',    # four-per-em space
    '\u2006',    # six-per-em space
    '\u2007',    # figure space
    '\u2008',    # punctuation space
    '\u2009',    # thin space
    '\u200A',    # hair space
    '\u2028',    # line separator
    '\u2029',    # paragraph separator
    '\u202F',    # narrow no-break space
    '\u205F',    # medium mathematical space
    '\u3000',    # ideographic space
    '\u180E',    # mongolian vowel separator
    '\u200B',    # zero width space
    '\u200C',    # zero width non-joiner
    '\u200D',    # zero width joiner
    '\u2060',    # word joiner
    '\uFEFF'])   # zero width non-breaking space


def cleanup(lines, skip_whitespace):
    '''Removes skippable content, shrinks multiple empty lines
    If a link only contains WHITESPACE,
    that line will get stripped of any WHITESPACE.'''

    id_lines = []
    if skip_whitespace:
        previous_blank = False
        for line in lines:
            if len(line.strip(WHITESPACE)) > 0:
                previous_blank = False
                keep = True
                for skip in SKIPS:
                    if skip.match(line):
                        keep = False
                        break
                if keep:
                    id_lines.append(line)
            elif not previous_blank:
                id_lines.append(line.strip(WHITESPACE))
                previous_blank = True
    else:
        for line in lines:
            keep = True
            for skip in SKIPS:
                if skip.match(line):
                    keep = False
                    break
            if keep:
                id_lines.append(line)
    return id_lines


def add_span(line, css_class):
    '''Add span tag with the class'''
    stripped_line = line.strip('\0+-^\1').strip(WHITESPACE)
    if len(stripped_line) == 0:
        return ''
    else:
        return escape(line). \
                    replace('\0+', '<span class="{}">'.format(css_class)). \
                    replace('\0-', '<span class="{}">'.format(css_class)). \
                    replace('\0^', '<span class="{}">'.format(css_class)). \
                    replace('\1', '</span>')


def get_wdiff(first_id_lines, second_id_lines):
    '''Return wdiff'''
    rows = ''
    seq = SequenceMatcher(isjunk=None,
                          a=first_id_lines,
                          b=second_id_lines)
    for tag, f1, f2, s1, s2 in seq.get_opcodes():
        if tag == 'equal':
            rows += escape(first_id_lines[f1:f2])
        elif tag == 'delete':
            rows += '<span class="w-delete">{}</span>'.format(
                        escape(first_id_lines[f1:f2]))
        elif tag == 'replace':
            rows += '<span class="w-delete">{}</span>'.format(
                        escape(first_id_lines[f1:f2]))
            rows += '<span class="w-insert">{}</span>'.format(
                        escape(second_id_lines[s1:s2]))
        elif tag == 'insert':
            rows += '<span class="w-insert">{}</span>'.format(
                        escape(second_id_lines[s1:s2]))
    output = '<pre>{}</pre>'.format(rows)

    return output


def get_diff_rows(first_id_lines, second_id_lines, context):
    '''Retuns diff rows'''
    rows = ''
    diffs = mdiff(first_id_lines, second_id_lines, context=context)
    contexts = 0
    for lb, rb, different in diffs:
        if not lb or not rb:
            rows += CONTEXT_LINE.format(context=contexts)
            contexts += 1
        elif not different:
            rows += UNCHANGED_ROW.format(
                                    lline=escape(lb[1]),
                                    rline=escape(rb[1]))
        else:
            lline = add_span(lb[1], 'delete')
            rline = add_span(rb[1], 'insert')
            if len(lline) > 0 or len(rline) > 0:
                rows += CHANGED_ROW.format(lline=lline, rline=rline)
    rows.replace('\t', '&nbsp;')

    return rows


def get_html_table(filename1, filename2, rows):
    '''Return HTML table'''
    return TABLE.format(filename1=escape(filename1),
                        filename2=escape(filename2),
                        rows=rows)


def get_iddiff(file1, file2, context_lines=None, table_only=False,
               wdiff=False, skip_whitespace=False):
    '''Return iddiff output'''

    title = 'Diff: {file1} - {file2}'.format(
                                        file1=escape(file1),
                                        file2=escape(file2))

    if wdiff:
        with open(file1, 'r') as file:
            id_a_lines = ''.join(cleanup(file.readlines(), skip_whitespace))
        with open(file2, 'r') as file:
            id_b_lines = ''.join(cleanup(file.readlines(), skip_whitespace))

        output = get_wdiff(id_a_lines, id_b_lines)

        output = HTML.format(output=output, title=title)
    else:
        with open(file1, 'r') as file:
            id_a_lines = cleanup(file.readlines(), skip_whitespace)
        with open(file2, 'r') as file:
            id_b_lines = cleanup(file.readlines(), skip_whitespace)

        rows = get_diff_rows(id_a_lines, id_b_lines, context_lines)

        output = get_html_table(file1, file2, rows)

        if not table_only:
            output = HTML.format(output=output, title=title)

    return output


def parse_args(args=None):
    '''Parse command line arguments and return options'''
    parser = ArgumentParser(description='Internet-Draft diff tool')

    main_group = parser.add_mutually_exclusive_group()
    main_group.add_argument('--side-by-side',
                            action='store_true',
                            default=True,
                            help='side by side difference (default)')
    main_group.add_argument('-w', '--wdiff',
                            action='store_true',
                            default=False,
                            help='produce word difference')

    group = parser.add_argument_group('side by side options')
    group.add_argument('-t', '--table-only',
                       action='store_true',
                       default=False,
                       help='produce only a HTML table')
    group.add_argument('-c', '--context-lines',
                       type=int,
                       default=8,
                       help='set number of context lines (set to 0 for no '
                            'context) (default 8)')

    parser.add_argument('-s', '--skip-whitespace',
                        action='store_true',
                        default=False,
                        help='skip multilines with only whitespace')
    parser.add_argument('--version',
                        action='version',
                        version='iddiff {}'.format(VERSION))

    parser.add_argument('file1', help='first file to compare')
    parser.add_argument('file2', help='second file to compare')

    return parser.parse_args(args)


def main():
    options = parse_args()

    file1 = options.file1
    file2 = options.file2
    if options.context_lines == 0:
        context_lines = None
    else:
        context_lines = options.context_lines

    try:
        iddiff = get_iddiff(file1=file1,
                            file2=file2,
                            context_lines=context_lines,
                            table_only=options.table_only,
                            wdiff=options.wdiff,
                            skip_whitespace=options.skip_whitespace)
        stdout.writelines(iddiff)
    except FileNotFoundError as e:
        stderr.write('iddiff: {}.\n'.format(e))
        exit(2)


if __name__ == '__main__':
    main()
