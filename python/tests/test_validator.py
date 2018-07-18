#!/usr/bin/env python
import unittest
import sys
import os
import copy

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import commandline_scripts.validatorSBtab as validator

class TestValidator(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]

        self.sbtabs = []
        self.sbtab_docs = []
        self.validate_table_objects = []
        self.validate_document_objects = []

        for i, t in enumerate(self.table_names):
            p = open('tables/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            sbtab_doc = SBtab.SBtabDocument('test_' + str(i), sbtab_init=p_content, filename=t)
            vt = validator.ValidateTable(sbtab)
            vt_doc = validator.ValidateDocument(sbtab_doc)
            self.validate_table_objects.append(vt)
            self.validate_document_objects.append(vt_doc)
            self.sbtabs.append(sbtab)
            self.sbtab_docs.append(sbtab_doc)
            p.close()

        for i, d in enumerate(self.doc_names):
            p = open('docs/' + d, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
            vt = validator.ValidateDocument(sbtab)
            self.validate_document_objects.append(vt)
            self.sbtab_docs.append(sbtab)
            p.close()

    def test_object_creation_table(self):
        '''
        test if the SBtabs can be used as input for the validator
        '''
        for i, vto in enumerate(self.validate_table_objects):
            
            # check if sbtab has arrived safely in validator
            self.assertEqual(self.sbtabs[i].header_row, vto.sbtab.header_row)
            self.assertEqual(self.sbtabs[i].columns, vto.sbtab.columns)
            self.assertEqual(self.sbtabs[i].columns_dict, vto.sbtab.columns_dict)
            self.assertEqual(self.sbtabs[i].value_rows, vto.sbtab.value_rows)
            self.assertEqual(self.sbtabs[i].table_type, vto.sbtab.table_type)

            # check if the variables are set correctly
            self.assertNotEqual(len(vto.allowed_table_types), 0)
            self.assertNotEqual(len(vto.allowed_columns), 0)
            self.assertNotEqual(len(vto.column2format), 0)
            self.assertEqual(sorted(vto.allowed_columns.keys()), sorted(vto.allowed_table_types))
            test_entries = []
            for entry in vto.allowed_columns[vto.sbtab.table_type]:
                test_entries.append(entry)
            self.assertEqual(sorted(vto.column2format.keys()), sorted(test_entries))
            for column in vto.allowed_columns:
                self.assertNotEqual(len(column), 0)
            self.assertNotIn('',vto.sbtab.columns)
            
    def test_object_creation_document(self):
        '''
        test if the SBtabs can be used as document input for the validator
        '''
        for i, vdo in enumerate(self.validate_document_objects):
            previous_doc = self.sbtab_docs[i]
            for j, sbtab in enumerate(vdo.sbtab_doc.sbtabs):
                previous_sbtab = previous_doc.sbtabs[j]
            
                # check if sbtab has arrived safely in validator
                self.assertEqual(previous_sbtab.header_row, sbtab.header_row)
                self.assertEqual(previous_sbtab.columns, sbtab.columns)
                self.assertEqual(previous_sbtab.columns_dict, sbtab.columns_dict)
                self.assertEqual(previous_sbtab.value_rows, sbtab.value_rows)
                self.assertEqual(previous_sbtab.table_type, sbtab.table_type)

    def test_single_validation_document(self):
        '''
        test if the single SBtabs of a document are used to build valid table objects
        '''
        for i, vdo in enumerate(self.validate_document_objects):
            vdo.validate_document()
            
            # check if the variables are set correctly
            self.assertNotEqual(len(vdo.vt.allowed_table_types), 0)
            self.assertNotEqual(len(vdo.vt.allowed_columns), 0)
            self.assertNotEqual(len(vdo.vt.column2format), 0)
            self.assertEqual(sorted(vdo.vt.allowed_columns.keys()), sorted(vdo.vt.allowed_table_types))
            for sbtab in vdo.sbtab_doc.sbtabs:
                self.assertNotIn('',sbtab.columns)
        
    def test_definition_file(self):
        '''
        test if the definition file is read correctly
        '''
        for vto in self.validate_table_objects:
            self.assertIsNotNone(vto.sbtab_def)
            self.assertIsNotNone(vto.definitions)
            self.assertNotEqual(len(vto.sbtab_def.header_row), 0)
            self.assertNotEqual(len(vto.sbtab_def.columns), 0)
            self.assertNotEqual(len(vto.sbtab_def.columns_dict), 0)
            self.assertNotEqual(len(vto.sbtab_def.value_rows), 0)
            self.assertNotEqual(len(vto.definitions[0]), 0)
            self.assertNotEqual(len(vto.definitions[1]), 0)
            self.assertNotEqual(len(vto.definitions[2]), 0)
            self.assertEqual(vto.sbtab_def.header_row, vto.definitions[0][0])
            self.assertEqual(vto.sbtab_def.columns, vto.definitions[1])
            self.assertEqual(vto.sbtab_def.value_rows, vto.definitions[2])

    def tearDown(self):
        '''
        close file/s
        '''
        for table in self.table_names:
            try:
                os.remove(table)
            except OSError:
                pass

        for doc in self.doc_names:
            try:
                os.remove(doc)
            except OSError:
                pass

    
if __name__ == '__main__':
    unittest.main()
