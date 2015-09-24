# -*- coding: utf-8 -*-

"""
tablib.dictionary.sbtab_dict
~~~~~~~~~~~~~

A wrapper object for handling an SBtab with multiple tables using
a dictinoary.
Also, includes methods for I/O between SQLite and SBtab.

"""
from SBtabTools import oneOrMany
from SBtab import SBtabTable, SBtabError
import tablib
from tablibIO import loadTSV
import sqlite3

class SBtabDict(dict):
    
    def __init__(self, sbtab_list):
        """
            Arguments:
                sbtab_list - a list of SBtabTable objects
        """
        self.fpath = ''
        self.sbtab_list = sbtab_list
        for m in sbtab_list:
            self[m.table_name] = m

    @staticmethod
    def FromSBtab(fpath):
        spreadsheet_file = loadTSV(fpath, False)
        m = oneOrMany(spreadsheet_file)
        sbtab_list = [SBtabTable(dset, fpath) for dset in m]
        sbtab_dict = SBtabDict(sbtab_list)
        sbtab_dict.fpath = fpath
        return sbtab_dict

    def GetColumnFromTable(self, table_name, column_name):
        """
            Returns:
                a list of the values in the column called 'column_name'
                in the table 'table_name'
        """
        column_index = self[table_name].columns_dict['!' + column_name]
        rows = self[table_name].getRows()
        return [r[column_index] for r in rows]

    def GetColumnsFromTable(self, table_name, column_names):
        """
            Arguments:
                table_name   - the name of the table in the SBtab file (without '!!')
                column_names - a list of column names from which to get the data (without '!')
                
            Returns:
                a list of lists containing the values corresponding to the
                columns in 'column_names' in the table 'table_name'
        """
        try:
            idxs = [self[table_name].columns_dict['!' + c] for c in column_names]
        except KeyError as e:
            all_columns = ', '.join(self[table_name].columns_dict.keys())
            raise KeyError('Cannot find the column %s in table "%s" in file %s. '
                           'Columns are: %s'
                           % (e, table_name, self.fpath, all_columns))
        return [map(r.__getitem__, idxs) for r in self[table_name].getRows()]
        
    def GetDictFromTable(self, table_name, key_column_name, value_column_name,
                         value_mapping=None):
        column_names = [key_column_name, value_column_name]
        keys, vals = zip(*self.GetColumnsFromTable(table_name, column_names))
        return dict(zip(keys, map(value_mapping, vals)))
        
    def GetTableAttribute(self, table_name, attribute_name):
        """
            Arguments:
                table_name     - the name of the table in the SBtab file (without '!!')
                attribute_name - a string with the attribute name
                
            Returns:
                A string containing the value of the attribute in that table,
                or None if the attribute does not exist
        """
        try:
            return self[table_name].getCustomTableInformation(attribute_name)
        except SBtabError:
            return None
            
    def SBtab2SQL(self, comm):
        comm.execute("DROP TABLE IF EXISTS __tables__")
        comm.execute("CREATE TABLE __tables__ (TableName TEXT, TableType TEXT, "
                     "header TEXT)")

        comm.execute("DROP TABLE IF EXISTS __columns__")
        comm.execute("CREATE TABLE __columns__ (TableName TEXT, idx INT, ColumnName TEXT)")

        for m in self.sbtab_list:
            # get the names of the columns in the right order (i.e. so that
            # the corresponding column indices will be 0..n)
            columns, _ = zip(*sorted(m.columns_dict.iteritems(), key=lambda x:x[1]))
            columns = list(columns)
            if '' in columns:
                columns.remove('')
            columns = map(lambda c: c[1:], columns)

            comm.execute("INSERT INTO __tables__ VALUES(?,?,?)", 
                         [m.table_name, m.table_type, m._getHeaderRow()])

            for i, col in enumerate(columns):
                comm.execute("INSERT INTO __columns__ VALUES(?,?,?)", 
                             [m.table_name, i, col])

            col_text = ','.join(['\'%s\' TEXT' % col for col in columns])
            comm.execute("DROP TABLE IF EXISTS %s" % m.table_name)
            comm.execute("CREATE TABLE %s (%s)" % (m.table_name, col_text))
            ins_command = "INSERT INTO %s VALUES(%s)" % \
                          (m.table_name, ','.join(["?"]*len(columns)))
            for row in m.getRows():
                comm.execute(ins_command, row)
        
        comm.commit()

    @staticmethod
    def FromSQLite(fpath):
        """
            Read all tables from a SQL database into an SBtab object.
            This function assumed that the database has one table
            called __tables__ with the relevant header fields for SBtab
        """
        comm = sqlite3.connect(fpath)
        assert list(comm.execute("SELECT name FROM sqlite_master WHERE name='__tables__'")) != []
        table_names, table_types, headers = \
            zip(*comm.execute("SELECT TableName, TableType, header from __tables__"))
        
        sbtabs = []
        for table_name, header in zip(table_names, headers):

            columns = []
            for c in comm.execute("SELECT ColumnName from __columns__ WHERE "
                                  "TableName == '%s' ORDER BY idx" % table_name):
                columns.append(c[0])
            
            sbtab = tablib.Dataset()
            sbtab.rpush([header] + [''] * (len(columns)-1))
            sbtab.rpush(map(lambda s: '!' + s, columns))
            for row in comm.execute("SELECT * FROM '%s'" % table_name):
                sbtab.append(row)
            sbtabs.append(sbtab)

        sbtab_list = [SBtabTable(dset, fpath) for dset in sbtabs]
        sbtab_dict = SBtabDict(sbtab_list)
        sbtab_dict.fpath = fpath
        return sbtab_dict
