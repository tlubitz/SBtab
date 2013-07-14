#!/usr/bin/env python
import SBtab
import tablibIO
import re

class SBtabError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class Validator:
    """
    Validator (version 0.1.0 07/12/2013)
    Check SBtab file and SBtab object.
    """
    def __init__(self, sbtab_table, sbtab_name):
        """
        Initialize validator and start check for file and table format.

        Parameters
        ----------
        table : tablib object
            Tablib object of the Sbtab file
        name : str
            File path of the Sbtab file
        """

        definition_table = tablibIO.importSet('./definitions/Definitions.csv')
        definitions = SBtab.SBtabTable(definition_table, './definitions/Definitions.csv')
        definitions.transposeTable()
        self.definitions = definitions.sbtab_dataset.dict[2:]

        for definition in self.definitions:
            while '' in definition:
                definition.remove('')

        self.warnings = ''
        self.table = sbtab_table
        self.filename = sbtab_name

        # check file format and header row
        self.validateFile()

        try:
            self.sbtab = SBtab.SBtabTable(self.table, self.filename)
        except:
            self.warnings += 'The Parser can not work with this file!'
            pass

        # check SBtab object for validity
        self.validate()

        if len(self.warnings) > 0:
            print self.warnings
                    # raise SBtabError(self.warnings)? why?
        else:
            print 'No warnings detected!'

    def validateFile(self):
        """
        Validate format of SBtab file, check file format and header row.
        """
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
                header + '\n'
        if not re.search('TableType="([^"])*"', header):
            self.warnings += 'The table type of the SBtab is not defined. Line: ' + \
                header + '\n'
        if not re.search('Table="([^"])*"', header):
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

    def validate(self):
        """
        Validate the table type and mandatory format of the SBtab.
        """
        # general stuff
        # 1st: check validity of table_type and save table type for later tests
        for table in self.definitions:
            if '!' + self.sbtab.table_type == table[0]:
                self.definitions = table
                break
            else:
                self.warnings += 'The SBtab file has an invalid TableType in its header: ' + \
                self.sbtab.table_type + '.\n'

        # 2nd: check the important first column
        first_column = '!' + self.sbtab.table_type
        if not self.rows_file[1][0] == first_column:
            self.warnings += 'The first column of the file does not correspond with the given TableType ' + \
                self.sbtab.table_type + 'and will be filled automatically.\n'

        # 3rd: check the validity of the given column names
        for i, column in enumerate(self.definitions[1:]):
            self.definitions[i] = '!' + column
        try:
            for column in self.sbtab.columns:
                if not column in self.definitions and not column.startswith('!MiriamID'):
                    self.warnings += 'The SBtab file has an unknown column: ' + \
                        column + '.\n'

            if not self.sbtab.columns_dict[self.definitions[0]] == 0:
                self.warnings += 'The SBtab primary column is at a wrong position.\n'
        except:
            self.warnings += 'The SBtab TableType is "unknown", therefor the main columns can not be checked! \n'

        # 4th: check the length of the different rows
        for row in self.sbtab.value_rows:
                # check the content of the main column (first one)
            if row[self.sbtab.columns_dict[self.definitions[0]]] == '':
                self.warnings += 'The SBtab includes a row with an undefined identifier in the main row: \n' + \
                    str(row) + '.\n'
                # raise SBtabError('The SBtab includes a row with an undefined
                # identifier in the main row: \n'+str(row))
            elif row[self.sbtab.columns_dict[self.definitions[0]]].startswith('+') or row[self.sbtab.columns_dict[self.definitions[0]]].startswith('-'):
                self.warnings += 'An identifier for a data row must not begin with "+" or "-": \n' + \
                    str(row) + '.\n'
                # raise SBtabError('An identifier for a data row must not begin
                # with "+" or "-": \n'+str(row))
            if ':' in row[self.sbtab.columns_dict[self.definitions[0]]] or '.' in row[self.sbtab.columns_dict[self.definitions[0]]]:
                self.warnings += 'An identifier for a data row must not include ":" or ".": \n' + \
                    str(row) + '.\n'
                # raise SBtabError('An identifier for a data row must not
                # include ":" or ".": \n'+str(row))
   
