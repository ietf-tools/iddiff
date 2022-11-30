from argparse import ArgumentParser
from difflib import _mdiff as mdiff
from html import escape
from pathlib import Path
from re import compile
from subprocess import Popen, PIPE
from string import whitespace
from sys import exit, stderr, stdout
from tempfile import NamedTemporaryFile

VERSION = '0.4.2'

WDIFF_ERROR = 'wdiff functionlity requires GNU Wdiff ' \
              '(https://www.gnu.org/software/wdiff/)\n'

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


def get_filename(filename):
    '''Return HTML escaped filename form user input path'''

    return escape(Path(filename).name)


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
        return line. \
                    replace('\0+', '<span class="{}">'.format(css_class)). \
                    replace('\0-', '<span class="{}">'.format(css_class)). \
                    replace('\0^', '<span class="{}">'.format(css_class)). \
                    replace('\1', '</span>')


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
                                    lline=lb[1],
                                    rline=rb[1])
        else:
            lline = add_span(lb[1], 'delete')
            rline = add_span(rb[1], 'insert')
            if len(lline) > 0 or len(rline) > 0:
                rows += CHANGED_ROW.format(lline=lline, rline=rline)
    rows.replace('\t', '&nbsp;')

    return rows


def get_html_table(filename1, filename2, rows):
    '''Return HTML table'''
    return TABLE.format(filename1=get_filename(filename1),
                        filename2=get_filename(filename2),
                        rows=rows)


def get_wdiff(file1, file2):
    '''Return wdiff output'''
    wdiff = ['wdiff', file1, file2]
    with Popen(args=wdiff, stdout=PIPE) as results:
        return results.communicate()[0].decode('utf-8')


def get_hwdiff(file1, file2):
    '''Return hwdiff output'''
    wdiff = ['wdiff', '-w', '<span class="w-delete">', '-x', '</span>', '-y',
             '<span class="w-insert">', '-z', '</span>', file1, file2]
    with Popen(args=wdiff, stdout=PIPE) as results:
        return results.communicate()[0].decode('utf-8')


def get_abdiff(file1, file2):
    '''Return before/after output'''
    diff = ['diff', '-d', '-U', '10000', file1, file2]
    result = ''
    section = 'HEADER'
    paragraph = 0
    old_para = ''
    new_para = ''
    updated = False
    section_re = [
                    compile(r'^\s\d+\..*(\w\s?)+$'),
                    compile(r'^\s(\w\s?)+$'),
                 ]
    newline_re = compile(r'^\s*$')
    with Popen(args=diff, stdout=PIPE) as results:
        diff_results = results.communicate()[0].decode('utf-8')
        for line in diff_results.split('\n')[3:]:
            if line.startswith('-'):
                old_para += '{}\n'.format(line[1:])
                updated = True
            elif line.startswith('+'):
                new_para += '{}\n'.format(line[1:])
                updated = True
            elif newline_re.match(line):
                if updated and (len(old_para) > 0 or len(new_para) > 0):
                    result += '\n{section}, Paragraph: {paragraph}\n'.format(
                                section=section,
                                paragraph=paragraph)
                    result += 'OLD:\n'
                    if len(old_para.strip()) > 0:
                        result += old_para
                    result += '\nNEW:\n'
                    if len(new_para.strip()) > 0:
                        result += new_para
                paragraph += 1
                old_para = ''
                new_para = ''
                updated = False
            else:
                for regex in section_re:
                    if regex.match(line):
                        section = line[1:]
                        old_para = ''
                        new_para = ''
                        paragraph = 0
                        updated = False
                else:
                    old_para += '{}\n'.format(line[1:])
                    new_para += '{}\n'.format(line[1:])

        return result


def get_chbars(file1, file2):
    '''Return change bars output'''
    diff = ['diff', '-B', '-d', '-U', '10000', file1, file2]
    grep = ['grep', '-v', '^-']
    tail = ['tail', '-n', '+3']
    sed = ['sed', 's/^+/|/']
    with Popen(args=diff,
               stdout=PIPE) as diff_results:
        with Popen(args=grep,
                   stdin=diff_results.stdout,
                   stdout=PIPE) as grep_results:
            with Popen(args=tail,
                       stdin=grep_results.stdout,
                       stdout=PIPE) as tail_results:
                with Popen(args=sed,
                           stdin=tail_results.stdout,
                           stdout=PIPE) as sed_results:
                    return sed_results.communicate()[0].decode('utf-8')


def get_iddiff(file1, file2, context_lines=None, table_only=False,
               wdiff=False, hwdiff=False, chbars=False, abdiff=False,
               skip_whitespace=False):
    '''Return iddiff output'''

    title = 'Diff: {file1} - {file2}'.format(
                                        file1=get_filename(file1),
                                        file2=get_filename(file2))
    tempfile1 = NamedTemporaryFile()
    tempfile2 = NamedTemporaryFile()
    with open(file1, 'r') as file:
        id_a_lines = cleanup(file.readlines(), skip_whitespace)
        if wdiff or chbars or abdiff:
            tempfile1.write(''.join(id_a_lines).encode('utf-8'))
        else:
            tempfile1.write(escape(''.join(id_a_lines)).encode('utf-8'))
        tempfile1.seek(0)
    with open(file2, 'r') as file:
        id_b_lines = cleanup(file.readlines(), skip_whitespace)
        if wdiff or chbars or abdiff:
            tempfile2.write(''.join(id_b_lines).encode('utf-8'))
        else:
            tempfile2.write(escape(''.join(id_b_lines)).encode('utf-8'))
        tempfile2.seek(0)

    if chbars:
        output = get_chbars(tempfile1.name, tempfile2.name)
    elif wdiff:
        output = get_wdiff(tempfile1.name, tempfile2.name)
    elif hwdiff:
        output = '<pre>{}</pre>'.format(
                    get_hwdiff(tempfile1.name, tempfile2.name))
        output = HTML.format(output=output, title=title)
    elif abdiff:
        output = get_abdiff(tempfile1.name, tempfile2.name)
    else:
        with open(tempfile1.name, 'r') as file:
            id_a_lines = file.readlines()
        with open(tempfile2.name, 'r') as file:
            id_b_lines = file.readlines()

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
    main_group.add_argument('--wdiff',
                            action='store_true',
                            default=False,
                            help='produce word difference '
                                 '(requries GNU Wdiff)')
    main_group.add_argument('--hwdiff',
                            action='store_true',
                            default=False,
                            help='produce HTML wrapped word difference '
                                 '(requires GNU Wdiff)')
    main_group.add_argument('--chbars',
                            action='store_true',
                            default=False,
                            help='produce changebar marked output')
    main_group.add_argument('--abdiff',
                            action='store_true',
                            default=False,
                            help='produce before/after output')

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
    parser.add_argument('-v', '--version',
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
                            hwdiff=options.hwdiff,
                            chbars=options.chbars,
                            abdiff=options.abdiff,
                            skip_whitespace=options.skip_whitespace)
        stdout.writelines(iddiff)
    except FileNotFoundError as e:
        if e.filename == 'wdiff':
            stderr.write(WDIFF_ERROR)  # pragma: no cover
        else:
            stderr.write('iddiff: {}.\n'.format(e))
        exit(2)


if __name__ == '__main__':
    main()  # pragma: no cover
