from argparse import ArgumentParser
from difflib import HtmlDiff
from re import compile
from sys import stdout

SKIPS = [
    compile(r'^.*\[?[Pp]age [0-9ivx]+\]?[ \t\f]*$'),
    compile(r'^ *Internet.Draft.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *INTERNET.DRAFT.+[12][0-9][0-9][0-9] *$'),
    compile(r'^ *Draft.+(  +)[12][0-9][0-9][0-9] *$'),
    compile(r'^RFC[ -]?[0-9]+.*(  +).* [12][0-9][0-9][0-9]$'),
    compile(r'^draft-[-a-z0-9_.]+.*[0-9][0-9][0-9][0-9]$')]


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

    html_diff = HtmlDiff()
    html_diff._styles = """
        table.diff {font-family:monospace; border:medium;}
        .diff_header {background-color:#e0e0e0}
        td.diff_header {text-align:right}
        .diff_next {background-color:#c0c0c0}
        .diff_add {background-color:#aaffaa}
        .diff_chg {background-color:#ffff77}
        .diff_sub {background-color:#ffaaaa}"""
    diff = html_diff.make_file(id_a_lines, id_b_lines, context=True)

    stdout.writelines(diff)


if __name__ == '__main__':
    main()
