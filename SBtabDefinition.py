#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import tablibIO
import os

class DefinitionTable:
    """
    Definition table (version 0.1.0 15/02/2014)
    Create SBtab definition table objects.
    
    Facilitates the handling with the definition table and provides informations for the validator. 
    """
    def __init__(self, filepath='./definitions/Definition.csv'):
        """
        Initialise defintion table object

        Parameter
        ---------
        filepath : string
            path of the definition table
            default = ./definitions/Definition.csv
        """
        self.filepath = filepath
        self.definition_table = self.loadTable(self.filepath).dict
        self.table_types = self.getTableTypes()
        self.table_columns = self.getTableColumns()

    def loadTable(self, filepath):
        """
        Import the definition table as Tablib object.

        Parameter
        ---------
        filepath : string
            path of the definition table

        Return
        ------
        dataset : tablib object
            tablib object (empty, if file not found)
        """
        if not os.path.isfile(filepath):
            print "File not found. File: " + filepath + " not found." 
            dataset = tablibIO.tablib.Dataset()
        else: 
            dataset = tablibIO.importSet(filepath)
            
        return dataset

    def getTableTypes(self):
        """
        Return set of valid table types.

        Return
        ------
        tabletypes : set
            list of valid table types
        """
        tabletypes = set()
        for row in self.definition_table:
            if row[0].startswith('!') and not row[0].startswith('!!'):
                tabletypes.add(row[0])
        return tabletypes

    def getTableColumns(self):
        """
        Return valid table columns for every valid table type.

        Return
        ------
        tablecolumns : dict
            dict of valid column names for every table type
        """
        tablecolumns = {}
        # create dict entry for every table type
        for name in self.table_types:
            tablecolumns[name] = {}
        # add valid columns
        for name in tablecolumns.keys():
            for row in self.definition_table:
                if row[0] == name:
                    tablecolumns[name][row[1]] = row[2:]
        return tablecolumns