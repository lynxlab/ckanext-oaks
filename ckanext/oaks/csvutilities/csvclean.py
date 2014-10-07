#!/usr/bin/env python

from os.path import splitext

from csvkit import CSVKitReader, CSVKitWriter
from csvkit.cli import CSVKitUtility 
from csvkit.cleanup import RowChecker

class CSVClean(CSVKitUtility):
    description = 'Fix common errors in a CSV file.'
    override_flags = ['H']
#    file_name


    def __init__(self, input_file=None):
        CSVKitUtility.__init__(self)
        self.file_name = input_file
        
        
    def add_arguments(self):
        self.argparser.add_argument('-n', '--dry-run', dest='dryrun', action='store_true',
            help='Do not create output files. Information about what would have been done will be printed to STDERR.')

    def main(self, dryRun):
#        reader = CSVKitReader(self.input_file, **self.reader_kwargs)
        reader = CSVKitReader(self.file_name)
        csvErrorCheked = ''
        
        print 'dryRun: '
        print dryRun
        print '....\n'
        print reader

        if dryRun:
            checker = RowChecker(reader)

            for row in checker.checked_rows():
                pass
            
            if checker.errors:
                for e in checker.errors:
#                    self.output_file.write('Line %i: %s\n' % (e.line_number, e.msg))
                    csvErrorCheked += ('Line %i: %s\n' % (e.line_number, e.msg))
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

def launch_new_instance():
    utility = CSVClean()
    utility.main()
    
if __name__ == '__main__':
    launch_new_instance()

