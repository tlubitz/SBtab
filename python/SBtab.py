#!/usr/bin/env python
'''
SBtab
=====
SBtab is a uniforming table format and designed for the use in
Systems Biology. Furthermore, it is a useful format to import stored
information into Python objects to process and manipulate it.

See specification for further information.
'''
import re
import csv
from io import StringIO
import logging
try:
    from . import misc
except:
    import misc


class SBtabError(Exception):
    '''
    Base class for errors in the SBtab class.
    '''
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class SBtabTable():
    '''
    SBtabTable (version 0.9.0 06/10/2010)
    '''
    def __init__(self, table_string, filename):
        '''
        Creates SBtab Python object from tablib object.

        Parameters
        ----------
        table : str
            Containing one SBtab, uncut. Directly from f.read().
        filename : str
            Filename with extension.
        '''
        self.filename = filename
        self.table_string = table_string

        # validate file extension
        self.validate_extension()

        # process string
        self.delimiter = misc.check_delimiter(table_string)
        self.table = self.cut_table_string(table_string)

        # Initialise table
        self.initialize_table()

    def validate_extension(self, test=None):
        '''
        Checks the extension of the file for invalid formats.
        '''
        valid_extensions = ['tsv', 'csv', 'xlsx']
        if test: filename = test
        else: filename = self.filename

        if filename[-3:] not in valid_extensions and filename[-4:] not in valid_extensions :
            raise SBtabError('The file extension is not valid for an SBtab file.')

        return True
        
    def cut_table_string(self, table_string, delimiter_test=None):
        '''
        the SBtab is initially given as one long string;
        cut down string into list to harvest content
        '''
        if delimiter_test: delimiter = delimiter_test
        else: delimiter = self.delimiter

        table_list = []
        for row in table_string.split('\n'):
            if row.replace(delimiter, '') != '':
                if not row.startswith('"!') and not row.startswith('!'):
                    if '"' in row:
                        if delimiter == ',' or delimiter == ';':
                            c_row = row.split('"')
                            no_quote_row = c_row[0][:-1].split(delimiter) + ['"'+c_row[1]+'"'] + c_row[2][1:].split(delimiter)
                            table_list.append(no_quote_row)
                        else: table_list.append(row.split(delimiter))
                    else: table_list.append(row.split(delimiter))
                else:
                    table_list.append(row.split(delimiter))

        return table_list

    def return_table_string(self):
        '''
        sometimes the file is required as a string (e. g. for
        writing files to harddisk; return string
        '''
        table_string = [self.header_row]
        table_string.append('\t'.join(self.columns))
        for row in self.value_rows:
            table_string.append('\t'.join(row))
        return '\n'.join(table_string)

    def initialize_table(self):
        '''
        Loads table informations and class variables.
        '''

        # read a potential document row
        self.doc_row = self._get_doc_row()

        # Read the header row from table
        self.header_row = self._get_header_row()

        # Read the table information from header row
        (self.table_type,
         self.table_name,
         self.table_document,
         self.table_version) = self.get_table_information()

        # Read the columns of the table
        (self.columns, self.columns_dict) = self.get_columns()

        # Read data rows
        self.value_rows = self.get_rows()

    def _get_doc_row(self):
        '''
        see if the SBtab Table holds a !!!-line to declare a belonging SBtab
        document
        '''
        doc_row_dq = False
        for row in self.table:
            for entry in row:
                if str(entry).startswith('!!!'):
                    doc_row = row
                    doc_row_dq = self.dequote(doc_row)
                    return doc_row_dq
                elif str(entry).startswith('"!!!'):
                    rm1 = row.replace('""', '#')
                    rm2 = row.remove('"')
                    doc_row = rm2.replace('#', '"')
                    doc_row_dq = self.dequote(doc_row)
                    return doc_row_dq
    
    def _get_header_row(self):
        '''
        Extracts the declaration row from the SBtab file.
        '''
        header_row = None
        # Find header row
        for row in self.table:
            for entry in row:
                if str(entry).startswith('!!'):
                    header_row = row
                    break
                elif str(entry).startswith('"!!'):
                    rm1 = row.replace('""', '#')
                    rm2 = row.remove('"')
                    header_row = rm2.replace('#', '"')
                    break

        # Save string or raise error
        if not header_row:
            raise SBtabError('''This is not a valid SBtab table, please use
            validator to check format or have a look in the specification!''')
        else:
            header_row = ' '.join(header_row)

        header_row_dq = self.dequote(header_row)

        return header_row_dq
            
    def dequote(self, row):
        '''
        bring consistency in the multifarious quotation mark problems
        '''
        stupid_quotes = ['"', '\xe2\x80\x9d', '\xe2\x80\x98', '\xe2\x80\x99',
                         '\xe2\x80\x9b', '\xe2\x80\x9c', '\xe2\x80\x9f',
                         '\xe2\x80\xb2', '\xe2\x80\xb3', '\xe2\x80\xb4',
                         '\xe2\x80\xb5', '\xe2\x80\xb6', '\xe2\x80\xb7', '”']

        for squote in stupid_quotes:
            try: row = row.replace(squote, "'")
            except: pass

        return row

    def get_table_information(self):
        '''
        Reads declaration row and stores the SBtab table attributes.
        '''
        no_name_counter = 0

        # Save table type, otherwise raise error
        try: table_type = self.get_custom_table_information('TableType')
        except: raise SBtabError('The TableType of the SBtab is not defined!')

        # Save table name, otherwise create name
        try: table_name = self.get_custom_table_information('TableName')
        except:
            table_name = table_type.capitalize() + '_unnamed'
            self.header_row += " TableName='" + table_name + "'"

        # Save table document, otherwise return None
        try: table_document = self.get_custom_table_information('Document')
        except: table_document = None

        # save table version, otherwise return None
        try: table_version = self.get_custom_table_information('SBtabVersion')
        except: table_version = None

        return table_type, table_name, table_document, table_version

    def get_custom_table_information(self, attribute_name):
        '''
        Retrieves the value of a table attribute in the declaration line

        Parameters
        ----------
        attribute_name : str
           Name of the table attribute.
        '''
        if re.search("%s='([^']*)'" % attribute_name,
                     self.header_row) is not None:
            return re.search("%s='([^']*)'" % attribute_name,
                             self.header_row).group(1)
        else:
            raise SBtabError('''The %s of the SBtab is
                                not defined!''' % attribute_name)

    def get_columns(self):
        '''
        Extract column headers, add mandatory first column name if necessary.
        '''
        # Save list of main columns
        for row in self.table:
            for entry in row:
                if str(row[0]).startswith('!') \
                   and not str(row[0]).startswith('!!'):
                    column_names = list(filter(lambda a: a != '', row))
                    break

        # Get column positions
        columns = {}
        for i, column in enumerate(column_names):
            columns[column] = i

        return column_names, columns

    def get_rows(self):
        '''
        Extract the rows of the SBtab
        '''
        value_rows = []
        # Add to comments, if row starts with '%'
        self.comments = []

        for row in self.table:
            if str(row[0]).startswith('!'):
                continue
            elif str(row[0]).startswith('%'):
                self.comments.append(list(row))
            else:
                value_rows.append(list(row)[:len(self.columns)])

        return value_rows


    # Here, the SBtab API actually starts
    
    def change_value(self, row, column, new):
        '''
        Change single value in the SBtab table by position in the table.

        Parameters
        ----------
        row : int
            Number of rows in the table. First row is number 1.
        column : int
            Number of columns in the table. First column is number 1.
        new : str
            New entry.
        '''
        try: self.value_rows[row - 1]
        except:
            raise SBtabError('The SBtab has only %s rows.' % len(self.value_rows))
        try: self.columns[column - 1]
        except:
            raise SBtabError('The SBtab has only %s columns.' % len(self.columns))
        
        try: self.value_rows[row - 1][column - 1] = str(new)
        except:
            raise SBtabError('Could not set the given value.')

        return True
        
    def change_value_by_name(self, name, column_name, new):
        '''
        Change singe value in the SBtab by name of column
        and of the first row entry.

        Parameters
        ----------
        row : str
            Name of the entry in the first column.
        column : str
            Name of the column (with '!')
        new : str
            New entry.
        '''
        try: self.columns_dict[column_name]
        except:
            raise SBtabError('The column %s is not in the SBtab.' % column_name)

        success = False
        col = self.columns_dict[column_name]
        for r in self.value_rows:
            if r[0] == name:
                r[col] = str(new)
                success = True

        if not success:
            raise SBtabError('Row %s was not found in the SBtab.' % name)

        return True

    def create_list(self):
        '''
        Creates a list object of the SBtab Python object.
        '''
        # Create new list
        sbtab_list = []

        # Append the parts header row, main column row and
        # value rows to the list
        sbtab_list.append([self.header_row])
        sbtab_list.append(self.columns)
        sbtab_list.append(self.value_rows)

        return sbtab_list

    def add_row(self, row_list, position=None):
        '''
        Adds row to the table, if postion is None at the end of it.

        Parameters
        ----------
        row_list : list
            List of strings, containing the entries of the new row.
        position : int
            Position of new row in the table, 0 is on top.
        '''
        if type(row_list) != list:
            raise SBtabError('%s is not a list' % row_list)

        if len(row_list) != len(self.columns):
            raise SBtabError('Given row %s has not the correct length.' % row_list)

        if position != None and type(position) != int:
            raise SBtabError('Please provide an integer row position.')

        for element in row_list:
            if type(element) != str:
                raise SBtabError('Please only provide string elements in the list')

        # If no position is set, add new row to the end
        if position is None:
            self.value_rows.append(row_list)
        else:
            self.value_rows.insert(position, row_list)

        return True

    def remove_row(self, position):
        '''
        Removes row from the table

        Parameters
        ----------
        position : int
            Position of row to be removed. Starting with 1.
        '''
        if not type(position) == int:
            raise SBtabError('Please provide an integer row position.')

        if position > len(self.value_rows):
            raise SBtabError('The SBtab only has %s row/s.' % len(self.value_rows))
       
        del self.value_rows[position-1]

        return True

    def add_column(self, column_list, position=None):
        '''
        Adds a column to the table, if position is None at the end of it.

        Parameters
        ----------
        column_list : list
            List of strings, containing the entries of the new column.
        position : int
            Position of new column in the table, 0 is right.
        '''
        if type(column_list) != list:
            raise SBtabError('%s is not a list' % column_list)
        
        if len(column_list) != (len(self.value_rows) + 1):
            raise SBtabError('The given column list has not the correct length.')

        if position != None and type(position) != int:
            raise SBtabError('Please provide an integer column position.')
                
        # If no position is set, add new column to the end
        if not position:
            for i, row in enumerate(self.value_rows):
                row.append(str(column_list[i + 1]))
            self.columns_dict[str(column_list[0])] = len(self.columns)
            self.columns.append(str(column_list[0]))
        else:
            for i, row in enumerate(self.value_rows):
                row.insert(position - 1, str(column_list[i + 1]))
            self.columns_dict[str(column_list[0])] = position - 1
            self.columns.insert(position - 1, str(column_list[0]))

        return True

    def remove_column(self, position):
        '''
        Removes column from the table.

        Parameters
        ----------
        position : int
            Position of column to be removed. Sarting with 1.
        '''
        if type(position) != int:
            raise SBtabError('Please provide an integer column position.')
        
        if position > len(self.columns):
            raise SBtabError('There are only %s columns in the SBtab' % str(len(self.columns)))
        
        # Remove entries on position
        for row in self.value_rows:
            del row[position - 1]
            
        # Remove column from column list
        column_to_remove = self.columns[position - 1]
        del self.columns[position - 1]

        # Remove column from columns dict
        self.columns_dict.pop(column_to_remove)

        return True

    def write(self, filename):
        '''
        write SBtab to hard disk
        '''
        if type(filename) != str:
            raise SBtabError('Please provide a filename as string.')
        
        if not filename.endswith('tsv') and not filename.endswith('csv'):
            if self.delimiter == '\t': filename += '.tsv'
            elif self.delimiter == ',': filename += '.csv'
            elif self.delimiter == ';': filename += '.csv'
            else:
                raise SBtabError('The file extension is missing and the '\
                                 'delimiter is no standard.')

        try:
            f = open(filename, 'w')
            f.write(self.return_table_string())
            f.close()
            return True
        except:
            raise SBtabError('The file could not be written.')

    def transpose_table(self):
        '''
        Transposes SBtab table. Switches columns and rows.
        '''
        # Initialize new table data
        trans_columns = []
        trans_columns_dict = {}
        trans_value_rows = []

        # Save old table data
        columns = self.columns
        value_rows = self.value_rows

        # Append first entry to new column
        trans_columns.append(columns.pop(0))

        # Set new rows
        for column in columns:
            trans_value_rows.append([column])

        # Set new values in tables
        for row in value_rows:
            trans_columns.append(row.pop(0))
            for i, entry in enumerate(row):
                trans_value_rows[i].append(entry)

        # Write new columns dict
        for i, column in enumerate(trans_columns):
            trans_columns_dict[column] = i

        # Overwrite old table data
        self.columns = trans_columns
        self.columns_dict = trans_columns_dict
        self.value_rows = trans_value_rows

        return True
    
    def to_data_frame(self):
        '''
        Exports SBtab table object as pandas dataframe
        '''
        try:
            import pandas as pd
            rows = self.get_rows()
            n_cols = max(map(len, rows))
            column_names = list(map(lambda s: s[1:], self.columns))
            while len(column_names) < n_cols:
                column_names += ['Col%d' % len(column_names)]
            df = pd.DataFrame(data=self.get_rows(), columns=column_names)
            return df
        except:
            raise SBtabError('Pandas dataframe could not be built.')

    @staticmethod
    def from_data_frame(df, document_name, table_type, table_name,
                        document, unit, sbtab_version='1.0'):
        table_string = StringIO()
        csv_writer = csv.writer(table_string, delimiter=',')

        header = [('DocumentName', document_name),
                  ('TableType', table_type),
                  ('TableName', table_name),
                  ('Document', document),
                  ('Unit', unit),
                  ('SBtabVersion', sbtab_version)]
        
        header_strings = ['!!SBtab'] + list(map(lambda x: "%s='%s'" % x, header))
        
        csv_writer.writerow([' '.join(header_strings)] + [''] * (df.shape[1]-1))
        csv_writer.writerow(map(lambda s: '!' + s, df.columns))
        csv_writer.writerows([row.tolist() for _, row in df.iterrows()])
        table_string.flush()
        
        return SBtabTable(table_string.getvalue(), 'unnamed_sbtab.tsv')


class SBtabDocument:
    '''
    The SBtab document class can consist of one or more SBtab Table objects
    '''
    def __init__(self, name, sbtab_init=None, filename=None):
        '''
        simple initialisation of SBtabDocument with an optional SBtab Table object
        '''
        self.name = name
        self.filename = filename
        self.sbtabs = []
        self.name_to_sbtab = {}
        self.type_to_sbtab = {}
        self.doc_row = False
        self.sbtab_filenames = []

        # if there is an initial sbtab given, see if it is
        # a string or an SBtab object
        if sbtab_init and type(sbtab_init) == str:
            self.add_sbtab_string(sbtab_init, filename)
        elif sbtab_init:
            self.add_sbtab(sbtab_init)
        
    def add_sbtab(self, sbtab):
        '''
        add an SBtab Table object to the SBtab Document
        '''
        if sbtab.filename in self.sbtab_filenames:
            raise SBtabError('The SBtab could not be added it has the '
                            'same table name as an existing SBtab:'
                            ' %s.' % (sbtab.filename))
            return

        if not self.filename:
            self.filename = sbtab.filename
          
        valid_type = self.check_type_validity(sbtab.table_type)
        if valid_type:
            self.name_to_sbtab[sbtab.table_name] = sbtab
            self.sbtabs.append(sbtab)
            self.sbtab_filenames.append(sbtab.filename)
            if sbtab.table_type in self.type_to_sbtab:
                tabs = self.type_to_sbtab[sbtab.table_type]
                tabs.append(sbtab)
                self.type_to_sbtab[sbtab.table_type] = tabs
            else:
                self.type_to_sbtab[sbtab.table_type] = [sbtab]

            self._get_doc_row_attributes()
            return True

    def add_sbtab_string(self, sbtab_string, filename):
        '''
        add one or multiple SBtab files as string
        '''
        # set filename if not given
        if not filename:
            sbtab_count = len(self.sbtabs)
            filename = 'unnamed_sbtab_%s.tsv'%(str(sbtab_count))

        # see if there are more than one SBtabs in the string
        try: sbtab_amount = misc.count_tabs(sbtab_string)
        except:
            raise SBtabError('The SBtab file could not be read properly.')

        # if there are more than one SBtabs, cut them in single SBtabs
        try:
            if sbtab_amount > 1:
                sbtab_strings = misc.split_sbtabs(sbtab_string)
                for i, sbtab_s in enumerate(sbtab_strings):
                    # here, we find a possible doc row
                    if sbtab_s.startswith('!!!'):
                        self.doc_row = sbtab_s
                        continue
                    
                    # then, go on with the cut SBtabs
                    name_single = str(i) + '_' + self.filename
                    sbtab_single = SBtabTable(sbtab_s, name_single)
                    logging.debug('name = %s, type = %s' % (sbtab_single.table_name, sbtab_single.table_type))
                    self.add_sbtab(sbtab_single)
            else:
                sbtab = SBtabTable(sbtab_string, filename)
                self.add_sbtab(sbtab)
        except Exception as e:
            raise SBtabError('The SBtab Table object could not be cre'\
                            'ated properly: ' + str(e))
        return True
            
    def check_type_validity(self, ttype):
        '''
        only certain table types are valid; this function checks if the
        given one is
        '''
        supported_types = ['Compound', 'Enzyme', 'Protein', 'Gene', 'Regulator',
                           'Compartment', 'Reaction', 'ReactionStoichiometry',
                           'Relation', 'Quantity', 'QuantityMatrix',
                           'Definition', 'PbConfig', 'Relationship',
                           'QuantityInfo', 'QuantityType', 'Position', 'FbcObjective']

        if ttype in supported_types:
            return True
        else:
            raise SBtabError('The table type %s is not supported.' % ttype)

    def _get_doc_row_attributes(self):
        '''
        read content of the !!!-document declaration row
        '''
        if not self.doc_row:
            self.doc_row = '!!!SBtab SBtabVersion="1.0" Document="%s"\n' % self.filename
        else:
            # save document name, otherwise raise error
            # (overrides name given at document initialisation)
            try: self.name = self.get_custom_doc_information('Document')
            except: pass

            # save SBtabVersion
            try: self.version = self.get_custom_doc_information('SBtabVersion')
            except: self.version = None
            
            # save date
            try: self.date = self.get_custom_doc_information('Date')
            except: self.date = None

            # save document type
            try: self.doc_type = self.get_custom_doc_information('DocumentType')
            except: self.doc_type = None
            
    def set_version(self, version):
        '''
        set SBtabVersion of the document
        '''
        try:
            self.version = version
        except:
            raise SBtabError('Version could not be set to %s' % version)
            
    def set_date(self, date):
        '''
        set date of the document
        '''
        try:
            self.date = date
        except:
            raise SBtabError('Date could not be set to %s' % date)
            
    def set_doc_type(self, doc_type):
        '''
        set doc_type of the document
        '''
        try:
            self.doc_type = doc_type
        except:
            raise SBtabError('Doc type could not be set to %s' % doc_type)
                    
    def remove_sbtab_by_name(self, name):
        '''
        remove SBtab Table from SBtab Document
        '''
        for i, sbtab in enumerate(self.sbtabs):
            if sbtab.table_name == name:
                del self.sbtabs[i]
                del self.name_to_sbtab[sbtab.table_name]
                del self.sbtab_filenames[i]
                tabs = self.type_to_sbtab[sbtab.table_type]
                for tab in tabs:
                    if tab.table_name == sbtab.table_name:
                        tabs.remove(tab)
                        break
        
                self.type_to_sbtab[sbtab.table_type] = tabs
                break
        return True

    def get_sbtab_by_name(self, name):
        '''
        return sbtab by given name
        '''
        try: return self.name_to_sbtab[name]
        except: return None

    def get_sbtab_by_type(self, ttype):
        '''
        returns list of sbtab objects by given table type
        '''
        try: return self.type_to_sbtab[ttype]
        except: return None

    def set_name(self, name):
        '''
        set name of SBtab Document
        '''
        self.name = name

    def write(self):
        '''
        write SBtabDocument to hard disk
        '''
        if not self.filename.endswith('tsv') and not self.filename.endswith('csv'):
            if self.delimiter == '\t': self.filename += '.tsv'
            elif self.delimiter == ',': self.filename += '.csv'
            elif self.delimiter == ';': self.filename += '.csv'
            else:
                raise SBtabError('The file extension is missing and the '\
                                 'delimiter is not set.')

        try:
            f = open(self.filename, 'w')
            f.write(self.doc_row)
            for sbtab in self.sbtabs:
                f.write(sbtab.return_table_string() + '\n\n')
            f.close()
            return True
        except:
            raise SBtabError('The file could not be written.')

        return True

    def get_custom_doc_information(self, attribute_name, test_row=None):
        '''
        Retrieves the value of a doc attribute in the doc line

        Parameters
        ----------
        attribute_name : str
           Name of the table attribute.
        '''
        if test_row: doc_row = test_row
        else: doc_row = self.doc_row
        
        if re.search("%s='([^']*)'" % attribute_name,
                     doc_row) is not None:
            return re.search("%s='([^']*)'" % attribute_name,
                             doc_row).group(1)
        else:
            raise SBtabError('''The %s of the Document is
                                not defined!''' % attribute_name)
        

    def set_doc_row(self, new_doc_row):
        '''
        set a new doc row
        '''
        if not new_doc_row.startswith('!!!SBtab'):
            raise SBtabError('A doc row needs to be preceded with "!!!SBtab".')

        if 'Document=' not in new_doc_row:
            raise SBtabError('A doc row needs to define the Document attribute.')

        self.doc_row = new_doc_row
        self._get_doc_row_attributes()
        
