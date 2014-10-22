#!/usr/bin/env python
from pylons.i18n.translation import _, ungettext
from csvkit.utilities.csvclean import CSVClean

from csvkit import CSVKitReader, CSVKitWriter
from csvkit.cleanup import RowChecker


import inspect
import sys

class OAKSClean(CSVClean):
    description = 'Fix common errors in a CSV file.'
    override_flags = ['H']
#    file_name


    def __init__(self, input_file=None, args=None, output_file=None):
 #       CSVClean.__init__(self)
        self.file_name = input_file

#    def __init__(self, args=None, output_file=None):
        """
        Perform argument processing and other setup for a CSVKitUtility.
        """
#         self._init_common_parser()
#         self.add_arguments()
#         self.args = self.argparser.parse_args(args)
        self.input_file = self._open_input_file(self.file_name)
        inspect.getdoc(self.input_file)

#         if 'f' not in self.override_flags:
#             self.input_file = self._open_input_file(self.args.input_path)

        self.reader_kwargs = self._extract_csv_reader_kwargs()
        self.writer_kwargs = self._extract_csv_writer_kwargs()

        self._install_exception_handler()

        if output_file is None:
            self.output_file = sys.stdout
        else:
            self.output_file = output_file

        # Ensure SIGPIPE doesn't throw an exception
        # Prevents [Errno 32] Broken pipe errors, e.g. when piping to 'head'
        # To test from the shell:
        #  python -c "for i in range(5000): print 'a,b,c'" | csvlook | head
        # Without this fix you will see at the end:
        #  [Errno 32] Broken pipe
        # With this fix, there should be no error
        # For details on Python and SIGPIPE, see http://bugs.python.org/issue1652
#         try:
#             import signal
#             signal.signal(signal.SIGPIPE, signal.SIG_DFL)
#         except (ImportError, AttributeError):
#             #Do nothing on platforms that don't have signals or don't have SIGPIPE
#             pass        
        
        
    def add_arguments(self):
        pass
#         self.argparser.add_argument('-n', '--dry-run', dest='dryrun', action='store_true',
#             help='Do not create output files. Information about what would have been done will be printed to STDERR.')

    def main(self, dryRun):
        reader = CSVKitReader(self.input_file, **self.reader_kwargs)
#         reader = CSVKitReader(self.file_name)
        csvErrorCheked = None
        
#         print 'dryRun: '
#         print dryRun
#         print '....\n'
#         print reader

        if dryRun:
            checker = RowChecker(reader)

            for row in checker.checked_rows():
                pass
            
            if checker.errors:
                csvErrorCheked = []
                for e in checker.errors:
#                    self.output_file.write('Line %i: %s\n' % (e.line_number, e.msg))
                    csvErrorCheked.append(_('Linea %i: %s\n') % (e.line_number+1, e.msg))                    
                    #csvErrorCheked += ('Line %i: %s\n' % (e.line_number, e.msg))
                    print csvErrorCheked
                return csvErrorCheked
#             else:
#                 self.output_file.write('No errors.\n')
            
            if checker.joins:
                self.output_file.write('%i rows would have been joined/reduced to %i rows after eliminating expected internal line breaks.\n' % (checker.rows_joined, checker.joins))
        else:
            base, ext = splitext(self.input_file.name)

            with open('%s_out.csv' % base,'w') as f:
                clean_writer = CSVKitWriter(f, **self.writer_kwargs)

                checker = RowChecker(reader)
                clean_writer.writerow(checker.column_names)

                for row in checker.checked_rows():
                    clean_writer.writerow(row)
            
            if checker.errors:
                error_filename = '%s_err.csv' % base

                with open(error_filename, 'w') as f:
                    error_writer = CSVKitWriter(f, **self.writer_kwargs)

                    error_header = ['line_number', 'msg']
                    error_header.extend(checker.column_names)
                    error_writer.writerow(error_header)

                    error_count = len(checker.errors)

                    for e in checker.errors:
                        error_writer.writerow(self._format_error_row(e))

                self.output_file.write('%i error%s logged to %s\n' % (error_count,'' if error_count == 1 else 's', error_filename))
            else:
                return 'Non ci sono errori'
                self.output_file.write('No errors.\n')

            if checker.joins:
                self.output_file.write('%i rows were joined/reduced to %i rows after eliminating expected internal line breaks.\n' % (checker.rows_joined, checker.joins))

    def _format_error_row(self, error):
        row = [error.line_number, error.msg]
        row.extend(error.row)

        return row
    
    def _extract_csv_reader_kwargs(self, delimiter= ','):
        """
        Extracts those from the command-line arguments those would should be passed through to the input CSV reader(s).
        """
        kwargs = {}
        if delimiter != ',':
            kwargs['delimiter'] = delimiter
            
#         if self.args.tabs:
#             kwargs['delimiter'] = '\t'
#         elif self.args.delimiter:
#             kwargs['delimiter'] = self.args.delimiter
# 
#         if self.args.quotechar:
#             kwargs['quotechar'] = self.args.quotechar
# 
#         if self.args.quoting:
#             kwargs['quoting'] = self.args.quoting
# 
#         if self.args.doublequote:
#             kwargs['doublequote'] = self.args.doublequote
# 
#         if self.args.escapechar:
#             kwargs['escapechar'] = self.args.escapechar
# 
#         if self.args.maxfieldsize:
#             kwargs['maxfieldsize'] = self.args.maxfieldsize
# 
#         if self.args.skipinitialspace:
#             kwargs['skipinitialspace'] = self.args.skipinitialspace
# 
#         if six.PY2 and self.args.encoding:
#             kwargs['encoding'] = self.args.encoding

        return kwargs
    
    def _extract_csv_writer_kwargs(self):
        """
        Extracts those from the command-line arguments those would should be passed through to the output CSV writer.
        """
        kwargs = {}

#         if 'l' not in self.override_flags and self.args.line_numbers:
#             kwargs['line_numbers'] = True

        return kwargs    

def launch_new_instance():
    utility = CSVClean()
    utility.main()
    
if __name__ == '__main__':
    launch_new_instance()

