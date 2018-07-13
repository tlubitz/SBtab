#!/usr/bin/env python
import unittest
import sys
import os
import copy

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import commandline_scripts.sbtab2sbml as sbtab2sbml

class TestSBtabTable(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]

        self.sbtab_docs = []
        self.convert_document_objects = []

        for i, t in enumerate(self.table_names):
            p = open('tables/' + t, 'r')
            p_content = p.read()
            sbtab_doc = SBtab.SBtabDocument('test_' + str(i), sbtab_init=p_content, filename=t)
            if 'Reaction' in sbtab_doc.type_to_sbtab.keys() or 'Compound' in sbtab_doc.type_to_sbtab.keys():
                conv = sbtab2sbml.SBtabDocument(sbtab_doc)
                self.convert_document_objects.append(conv)
                self.sbtab_docs.append(sbtab_doc)
            p.close()
            
        for i, d in enumerate(self.doc_names):
            p = open('docs/' + d, 'r')
            p_content = p.read()
            sbtab_doc = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
            if 'Reaction' in sbtab_doc.type_to_sbtab.keys() or 'Compound' in sbtab_doc.type_to_sbtab.keys():
                conv = sbtab2sbml.SBtabDocument(sbtab_doc)
                self.convert_document_objects.append(conv)
                self.sbtab_docs.append(sbtab_doc)
            p.close()

    def test_object_creation(self):
        '''
        test if the SBtabs have arrived safely
        '''
        for i, vto in enumerate(self.convert_document_objects):
            previous_sbtab_doc = self.sbtab_docs[i]
            self.assertEqual(previous_sbtab_doc, vto.sbtab_doc)
            self.assertEqual(previous_sbtab_doc.doc_row, vto.sbtab_doc.doc_row)
            self.assertEqual(previous_sbtab_doc.sbtabs, vto.sbtab_doc.sbtabs)
            for j, sbtab in enumerate(vto.sbtab_doc.sbtabs):
                previous_sbtab = previous_sbtab_doc.sbtabs[j]
                self.assertEqual(previous_sbtab, sbtab)
                self.assertEqual(previous_sbtab.header_row, sbtab.header_row)
                self.assertEqual(previous_sbtab.columns, sbtab.columns)
                self.assertEqual(previous_sbtab.columns_dict, sbtab.columns_dict)
                self.assertEqual(previous_sbtab.value_rows, sbtab.value_rows)
                self.assertEqual(previous_sbtab.table_type, sbtab.table_type)

    def test_conversion(self):
        '''
        test if the conversion can be processed
        '''
                
                
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
