from io import StringIO
from os.path import basename
from unittest import TestCase
from unittest.mock import patch
import sys

from iddiff.iddiff import (
        add_span, cleanup, get_diff_rows, get_filename, get_html_table,
        get_iddiff, get_hwdiff, main, parse_args)

HEADERS_AND_FOOTERS = """
Crocker                                                        [Page 5]
RFC 1                        Host Software                 7 April 1969
Reynolds & Postel                                               [Page 1]
RFC 1000 - Request for Comments Reference Guide              August 1987
Internet Architecture Board Standards Track                     [Page 1]
RFC 2000                   Internet Standards              February 1997
Internet-Draft                 Foo Bar                          May 2021
INTERNET-DRAFT                 Foo Bar                          May 2021
draft-foo-bar-01               Foo Bar                          May 2021
""".split('\n')[1:-1]

DEFAULT_ARGS = ['foo', 'bar']
LINES_A = [
        'Lorem ipsum dolor sit amet, consectetur adipiscing elit,',
        'sed do eiusmod tempor incididunt ut labore et dolore magna',
        'aliqua. Ut enim ad minim veniam, quis nostrud exercitation',
        'ullamco laboris nisi ut aliquip ex ea commodo consequat.']
LINES_B = LINES_A[:-1]

FILE_1 = 'tests/data/draft-smoke-signals-00.txt'
FILE_2 = 'tests/data/draft-smoke-signals-01.txt'


class TestIddiff(TestCase):
    '''Tests for iddiff'''

    def test_cleanup_shrink_empty_lines(self):
        lines = [' ', '', '\u0009', '\u2009\u200A ']

        output = cleanup(lines, skip_whitespace=True)

        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], '')

    def test_cleanup_keep_empty_lines(self):
        lines = [' ', '', '\u0009', '\u2009\u200A ']

        output = cleanup(lines, skip_whitespace=False)

        self.assertEqual(len(output), 4)
        for line in lines:
            self.assertIn(line, output)

    def test_cleanup_skippable_content(self):
        for skip_whitespace in (True, False):
            output = cleanup(HEADERS_AND_FOOTERS, skip_whitespace)

            self.assertEqual(len(output), 0)

    def test_cleanup_non_skippable_content(self):
        non_skippable = [
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit,    ',
            'sed do eiusmod tempor incididunt ut labore et dolore magna  ',
            'aliqua. Ut enim ad minim veniam, quis nostrud exercitation  ',
            'ullamco laboris nisi ut aliquip ex ea commodo consequat.    ']

        for skip_whitespace in (True, False):
            output = cleanup(HEADERS_AND_FOOTERS + non_skippable,
                             skip_whitespace)

            self.assertEqual(len(output), len(non_skippable))

            for line in non_skippable:
                self.assertIn(line, output)

    def test_add_span(self):
        lines = [
            'Lorem \0+ipsum\1 dolor sit amet, consectetur adipiscing elit,',
            'Lorem \0-ipsum\1 dolor sit amet, consectetur adipiscing elit,',
            'Lorem \0^ipsum\1 dolor sit amet, consectetur adipiscing elit,']

        for line in lines:
            output = add_span(line, 'foobar')

            self.assertIn('<span class="foobar">ipsum</span>', output)

    def test_add_span_empty_line(self):
        lines = [' ', '', '\u0009', '\u2009\u200A ']

        for line in lines:
            output = add_span(line, 'foobar')

            self.assertEqual(output, '')

    def test_get_diff_rows(self):
        lines_b = [
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit,',
            'sed do eiusmod incididunt ut labore et dolore magna',
            'aliqua. Ut enim add minim veniam, quis nostrud exercitation',
            'ullamco laboris nisi ut aliquip ex ea commodo consequat.']

        output = get_diff_rows(LINES_A, lines_b, context=None)

        # unchanged
        self.assertIn(LINES_A[0], output)
        self.assertIn(lines_b[0], output)

        # deletion
        self.assertNotIn(LINES_A[1], output)
        self.assertIn(lines_b[1], output)
        self.assertIn('<span class="delete"> tempor</span>', output)

        # insertion
        self.assertIn(LINES_A[2], output)
        self.assertNotIn(lines_b[2], output)
        self.assertIn('<span class="insert">d</span>', output)

    def test_get_diff_rows_with_context_lines(self):
        output = get_diff_rows(LINES_A, LINES_B, context=1)

        self.assertIn('Skipping', output)
        self.assertNotIn(LINES_A[0], output)
        self.assertNotIn(LINES_A[1], output)

    def test_get_hwdiff(self):
        lines_a = ''.join(LINES_A)
        lines_b = ''.join([
            'Lorem ipsum dolor sit amet, consectetur adipiscing elit,',
            'sed do eiusmod incididunt ut labore et dolore magna',
            'aliqua. Ut enim add minim veniam, quis nostrud exercitation',
            'ullamco laboris nisi ut aliquip ex ea commodo consequat.'])

        output = get_hwdiff(lines_a, lines_b)

        self.assertIn(LINES_A[0], output)
        self.assertIn('<span class="w-delete">', output)
        self.assertIn('<span class="w-insert">', output)

    def test_get_html_table(self):
        rows = get_diff_rows(LINES_A, LINES_B, context=None)
        table = get_html_table(filename1='foo',
                               filename2='bar',
                               rows=rows)

        self.assertTrue(table.strip().startswith('<table'))
        self.assertTrue(table.strip().endswith('table>'))
        self.assertIn('foo', table)
        self.assertIn('bar', table)
        self.assertIn(LINES_A[0], table)

    def test_arg_parse_table(self):
        self.assertFalse(parse_args(DEFAULT_ARGS).table_only)

        for arg in ['-t', '--table-only']:
            self.assertTrue(parse_args(DEFAULT_ARGS + [arg, ]).table_only)

    def test_arg_parse_lines(self):
        self.assertEqual(parse_args(DEFAULT_ARGS).context_lines, 8)

        for args in [['-c', '10'], ['--context-lines', '10']]:
            self.assertEqual(parse_args(DEFAULT_ARGS + args).context_lines, 10)

    def test_arg_parse_files(self):
        options = parse_args(DEFAULT_ARGS)

        self.assertEqual(options.file1, DEFAULT_ARGS[0])
        self.assertEqual(options.file2, DEFAULT_ARGS[1])

    def test_iddiff(self):
        output = get_iddiff(FILE_1, FILE_2,
                            context_lines=None, table_only=False)

        self.assertIn('<html', output)
        self.assertIn('<table', output)
        self.assertNotIn('>Skipping<', output)
        self.assertTrue(output.strip().endswith('</html>'))

    def test_iddiff_table_only(self):
        output = get_iddiff(FILE_1, FILE_2,
                            context_lines=None, table_only=True)

        self.assertNotIn('<html', output)
        self.assertNotIn('>Skipping<', output)
        self.assertTrue(output.strip().startswith('<table'))
        self.assertTrue(output.strip().endswith('</table>'))

    def test_iddiff_with_context(self):
        output = get_iddiff(FILE_1, FILE_2,
                            context_lines=8, table_only=False)

        self.assertIn('<html', output)
        self.assertIn('<table', output)
        self.assertIn('>Skipping<', output)
        self.assertTrue(output.strip().endswith('</html>'))

    def test_hwdiff(self):
        output = get_iddiff(FILE_1, FILE_2, hwdiff=True)

        self.assertIn('<html', output)
        self.assertIn('<pre', output)
        self.assertIn('class="w-delete"', output)
        self.assertIn('class="w-insert"', output)
        self.assertNotIn('<table', output)
        self.assertTrue(output.strip().endswith('</html>'))

    def test_iddiff_file_error(self):
        with self.assertRaises(FileNotFoundError):
            get_iddiff('foo', 'bar', None, False)

    def test_main(self):
        sys.argv = [basename(__file__), FILE_1, FILE_2]
        output = StringIO()
        with patch('sys.stdout.writelines', new=output.writelines):
            main()

        self.assertIn('<html', output.getvalue())
        self.assertIn('<table', output.getvalue())
        self.assertIn('>Skipping<', output.getvalue())
        self.assertTrue(output.getvalue().strip().endswith('</html>'))

    def test_main_table_only(self):
        sys.argv = [basename(__file__), '-t', FILE_1, FILE_2]
        output = StringIO()
        with patch('sys.stdout.writelines', new=output.writelines):
            main()

        self.assertNotIn('<html', output.getvalue())
        self.assertIn('>Skipping<', output.getvalue())
        self.assertTrue(output.getvalue().strip().startswith('<table'))
        self.assertTrue(output.getvalue().strip().endswith('</table>'))

    def test_main_with_without_context(self):
        sys.argv = [basename(__file__), '-c', 0, FILE_1, FILE_2]
        output = StringIO()
        with patch('sys.stdout.writelines', new=output.writelines):
            main()

        self.assertIn('<html', output.getvalue())
        self.assertIn('<table', output.getvalue())
        self.assertNotIn('>Skipping<', output.getvalue())
        self.assertTrue(output.getvalue().strip().endswith('</html>'))

    def test_main_file_error(self):
        sys.argv = [basename(__file__), 'foo', 'bar']
        output = StringIO()

        with self.assertRaises(SystemExit):
            with patch('sys.stderr.write', new=output.write):
                main()

        self.assertTrue(output.getvalue().startswith('iddiff:'))

    def test_get_filename(self):
        PATH_INPUTS = [
                'foobar.txt',
                'foobar/foobar.txt',
                'foo/bar/foobar.txt',
                '/foo/bar/foobar.txt',
                '../foo/bar/foobar.txt',
                './foobar.txt']

        for path in PATH_INPUTS:
            self.assertEqual(get_filename(path), 'foobar.txt')

    def test_chbars(self):
        output = get_iddiff(FILE_1, FILE_2, chbars=True)

        self.assertIn(' Network Working Group ', output)
        self.assertIn('|Internet-Draft ', output)
