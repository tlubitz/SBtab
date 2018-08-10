#!/usr/bin/env python
import unittest
import copy
import os
import sys
import libsbml

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import misc
import SBtab

class TestMiscFunctions(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]
        self.sbml_names = [f for f in os.listdir('sbml/') if os.path.isfile(os.path.join('sbml/', f))]
        
        self.sbtabs = []
        for t in self.table_names:
            p = open('tables/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

        self.docs = []
        for i, d in enumerate(self.doc_names):
            p = open('docs/' + d, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
            self.docs.append(sbtab)
            p.close()


        self.sbml_docs = []
        reader = libsbml.SBMLReader()
        for i, s in enumerate(self.sbml_names):
            if s.startswith('_'): continue
            doc = reader.readSBML('sbml/' + s)
            self.sbml_docs.append(doc)
            

    def test_tab_counter(self):
        '''
        test if the amount of SBtabs in one file can be determined
        '''
        for sbtab in self.sbtabs:
            amount = misc.count_tabs(sbtab.return_table_string())
            self.assertEqual(amount,1)

    def test_extension_validator(self):
        '''
        test if the file extension can be validated
        '''
        for sbtab_name in self.table_names:
            self.assertTrue(misc.validate_file_extension(sbtab_name, 'sbtab'))

        for sbtab_name in self.doc_names:
            self.assertTrue(misc.validate_file_extension(sbtab_name, 'sbtab'))
            
        for sbml_name in self.sbml_names:
            self.assertTrue(misc.validate_file_extension(sbml_name, 'sbml'))
        
        for bad_name in ['test.txt', 'test.xls', 'test.rtf', 'test.pdf', 'test.m']:
            self.assertFalse(misc.validate_file_extension(bad_name, 'sbml'))
            self.assertFalse(misc.validate_file_extension(bad_name, 'sbtab'))
    
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
