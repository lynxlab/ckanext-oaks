#!/usr/bin/env python
from pylons.i18n.translation import _, ungettext
from csvkit.utilities.in2csv import In2CSV
from csvkit import convert
from csvkit import CSVKitReader, CSVKitWriter

class OAKSIn2CSV(In2CSV):
    description = 'Convert common, but less awesome, tabular data formats to CSV.'
    epilog='Some command line flags only pertain to specific input formats.'
    override_flags = ['f']

    def __init__(self, input_file=None, args=None, output_file=None, filetype = None):
        self.file_name = input_file
        self.filetype = filetype
        self.csvResult = []
        self.output_file = open(output_file,'w')
        self.args = args
        self.reader_kwargs = self._extract_csv_reader_kwargs()
        self.writer_kwargs = self._extract_csv_writer_kwargs()
        
        self._install_exception_handler()

        if output_file is None:
            self.output_file = sys.stdout
        else:
            self.output_file = output_file
        

    def add_arguments(self):
        pass
#         self.argparser.add_argument(metavar="FILE", nargs='?', dest='input_path',
#             help='The CSV file to operate on. If omitted, will accept input on STDIN.')
#         self.argparser.add_argument('-f', '--format', dest='filetype',
#             help='The format of the input file. If not specified will be inferred from the file type. Supported formats: %s.' % ', '.join(sorted(convert.SUPPORTED_FORMATS)))
#         self.argparser.add_argument('-s', '--schema', dest='schema',
#             help='Specifies a CSV-formatted schema file for converting fixed-width files.  See documentation for details.')
#         self.argparser.add_argument('-k', '--key', dest='key',
#             help='Specifies a top-level key to use look within for a list of objects to be converted when processing JSON.')
#         self.argparser.add_argument('-y', '--snifflimit', dest='snifflimit', type=int,
#             help='Limit CSV dialect sniffing to the specified number of bytes. Specify "0" to disable sniffing entirely.')
#         self.argparser.add_argument('--sheet', dest='sheet',
#             help='The name of the XLSX sheet to operate on.')
#         self.argparser.add_argument('--no-inference', dest='no_inference', action='store_true',
#             help='Disable type inference when parsing the input.')

    def main(self):
        if self.filetype:
            filetype = self.filetype

            if filetype not in convert.SUPPORTED_FORMATS:
                self.csvResult = (_('"%s" is not a supported format') % self.filetype)

#         elif self.args.schema:
#             filetype = 'fixed'
#         elif self.args.key:
#             filetype = 'json'
        else:
            if not self.file_name or self.file_name == '-':
                self.csvResult = _('You must specify a format.')

            filetype = convert.guess_format(self.file_name)

            if not filetype:
                self.csvResult = _('Unable to automatically determine the format of the input file. Try specifying a format with --format.')

        if filetype in ('xls', 'xlsx'):
            self.input_file = open(self.file_name, 'rb')
        else:
            self.input_file = self._open_input_file(self.args.input_path)

        kwargs = self.reader_kwargs

#         if self.args.schema:
#             kwargs['schema'] = self._open_input_file(self.args.schema)
# 
#         if self.args.key:
#             kwargs['key'] = self.args.key
# 
#         if self.args.snifflimit:
#             kwargs['snifflimit'] = self.args.snifflimit
# 
#         if self.args.sheet:
#             kwargs['sheet'] = self.args.sheet
# 
#         if self.args.no_inference:
#             kwargs['type_inference'] = False
# 
#         if filetype == 'csv' and self.args.no_header_row:
#             kwargs['no_header_row'] = True
# 
#         # Fixed width can be processed as a stream
#         if filetype == 'fixed':
#             kwargs['output'] = self.output_file

        data = convert.convert(self.input_file, filetype, **kwargs)

        print 'out: '
        out_file_opened = open(self.output_file,'w')
        print out_file_opened
        out_file_opened.write(data)
        
        
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
    utility = In2CSV()
    utility.main()
    
if __name__ == "__main__":
    launch_new_instance()

