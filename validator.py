#!/usr/bin/env python
import SBtab
import tablibIO
import SBtabDefinition
import re

class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class ValidateTable:
    """
    Validator (version 0.2.0 15/02/2014)
    Check SBtab file and SBtab object.
    """
    def __init__(self, table, sbtab_name):
        """
        Initialize validator and start check for file and table format.

        Parameters
        ----------
        table : tablib object
            Tablib object of the Sbtab file
        sbtab_name : str
            File path of the Sbtab file
        """
        # import definitions from definition table
        try:
            definition_table = tablibIO.importSet('./definitions/Definitions.tsv')
            definition_sbtab = SBtab.SBtabTable(definition_table, './definitions/Definitions.tsv')
            # ignore header and main column
            self.definitions = definition_sbtab.sbtab_list
        except:
            raise SBtabError('Definition table could not be find, check file path! See specifications for further information.')

        # create set of valid table types
        self.allowed_table_types = list(set([row[1] for row in self.definitions[2:][0]]))
        # create dict of valid column names per table type
        self.allowed_columns = {}
        for table_type in self.allowed_table_types:
            self.allowed_columns[table_type] = [row[2] for row in self.definitions[2:][0] if row[1] == table_type]
        # initialize warning string
        self.warnings = ''
        # define self variables
        self.table = table
        self.filename = sbtab_name

        # check file format and header row
        self.checkTableFormat()

        # try creating SBtab instance
        try:
            self.sbtab = SBtab.SBtabTable(self.table, self.filename)
        except:
            print self.warnings
            raise SBtabError('The Parser can not work with this file!')

        # check SBtab object for validity
        self.checkTable()

        # print warnings
        if len(self.warnings) > 0:
            print self.warnings
        else:
            print 'No warnings detected!'

    def checkTableFormat(self):
        """
        Validate format of SBtab file, check file format and header row.
        """
        # Check tablib header
        if self.table.headers:
            self.warnings += 'Tablib header is set, will be removed. This feature is not supported.'
            self.table.headers = None
        # save table rows in variable
        self.rows_file = self.table.dict

        # save header row
        header_row = self.rows_file[0]
        while '' in header_row:
            header_row.remove('')
        header = ""
        for x in header_row[:-1]:
            header += x + ' '
        header += header_row[-1]

        # check for valid header row
        if not header.startswith('!!'):
            self.warnings += 'The header row of the table does not start with "!!SBtab": ' + \
                header + '\n \t This will cause an error! \n'
        if not re.search("!TableType='([^'])*'", header):
            self.warnings += 'The table type of the SBtab is not defined. Line: ' + \
                header + '\n \t This will cause an error! \n'
        if not re.search("!Table='([^'])*'", header):
            self.warnings += 'The name of the SBtab table is not defined. Line: ' + \
                header + '\n'

        # check for possible table content and main columns
        columns_row = self.rows_file[1]
        columns = ""
        for x in columns_row[:-1]:
            columns += x + ' '
        columns += columns_row[-1]
        # check length of table
        if len(self.rows_file) < 3:
            self.warnings += 'The table contains no information: ' + \
                header + '\n'
        else:
            self.main_column_count = None
            # checks for existing main column
            if not columns.startswith('!'):
                self.warnings += 'The main column row of the table does not start with "!": ' + \
                    columns + '\n'

    def checkTable(self):
        """
        Validate the table type and mandatory format of the SBtab.
        """
        column_check = True
        # general stuff
        # 1st: check validity of table_type and save table type for later tests
        if not '!' + self.sbtab.table_type in self.allowed_table_types:
            self.warnings += 'The SBtab file has an invalid TableType in its header: ' + self.sbtab.table_type + '.\n'
            column_check = False

        # 2nd: check the important first column
        first_column = '!' + self.sbtab.table_type
        if not self.rows_file[1][0] == first_column:
            self.warnings += 'The first column of the file does not correspond with the given TableType ' + \
                self.sbtab.table_type + 'and will be filled automatically.\n'

        # 3rd: check the validity of the given column names
        if column_check:
            for column in self.sbtab.columns:
                if not column.replace('!', '') in self.allowed_columns[self.sbtab.table_type] and not column.startswith('!MiriamID'):
                    self.warnings += 'The SBtab file has an unknown column: ' + \
                        column + '.\n \t Please use only supported column types!'
            if not self.sbtab.columns_dict['!' + self.sbtab.table_type] == 0:
                self.warnings += 'The SBtab primary column is at a wrong position.\n'
        else:
            self.warnings += 'The SBtab TableType is "unknown", therefore the main columns can not be checked! \n'

        # 4th: check the length of the different rows
        for row in self.sbtab.value_rows:
            # check the content of the main column (first one) for empty entries
            if row[self.sbtab.columns_dict['!' + self.sbtab.table_type]] == '':
                self.warnings += 'The SBtab includes a row with an undefined identifier in the row: \n' + str(row) + '.\n'
            for column in self.sbtab.columns:
                # check the rows for entries starting with + or -
                if row[self.sbtab.columns_dict[column]].startswith('+') or row[self.sbtab.columns_dict[column]].startswith('-'):
                    self.warnings += 'An identifier for a data row must not begin with "+" or "-": \n' + \
                        str(row) + '.\n'
                # check the rows for entries containing . or : 
                if ',' in list(row[self.sbtab.columns_dict[column]]):
                    self.warnings += 'An identifier for a data row must not include ".": \n' + \
                        str(row) + '.\n'
                    # raise SBtabError('An identifier for a data row must not
                    # include ":" or ".": \n'+str(row))

class ValidateFile:
    """
    Validate file and check for valid format.

    Notes
    -----
    To open a file: sbtab_file = open("filepath", "rb")
    """
    def __init__(self, sbtab_file, filename):
        # initialize warning string
        self.warnings = ""

        self.file = sbtab_file
        self.filename = filename

        self.validateExtension(self.filename)
        self.validateFile(self.file)

        # print warnings
        if len(self.warnings) > 0:
            print self.warnings
        else:
            print 'No warnings detected!'

    def validateExtension(self, filename):
        """
        Check the extension of the file for invalid formats.
        """
        if not (str(filename).endswith('.tsv') or str(filename).endswith('.csv') or str(filename).endswith('.ods') or str(filename).endswith('.xls')):
            self.warnings += 'The given file format is not supported: ' + filename + '. Please use ".tsv", ".csv", ".ods" or ".xls" instead.\n'

    def validateFile(self, sbtab_file):
        """
        Validate file format and check for possible problems.
        """
        rows = []
        for line in sbtab_file:
            rows.append(line)

        length = len(rows[0])
        for i, row in enumerate(rows):
            if not row:
                self.warnings += 'The file contains an empty row in line ' + str(i) + '\n Will be ignored. \n'
            if not len(row) == length:
                self.warnings += 'The lengths of the rows are not identical.\n Will be adjusted automatically. \n'
            length = len(row)
