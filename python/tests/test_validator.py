#!/usr/bin/env python
import unittest
import sys
import os

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import commandline_scripts.validatorSBtab as validator

class TestSBtabTable(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('tables/') if os.path.isfile(os.path.join('tables/', f))]
        self.doc_names = [f for f in os.listdir('docs/') if os.path.isfile(os.path.join('docs/', f))]

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

    def test_object_creation(self):
        '''
        test if the SBtabs can be used as input for the validator
        '''
        for sbtab in self.sbtabs:
            vt = validator.ValidateTable(sbtab)
        
        #self.assertTrue(random_sbtab.validate_extension(test=c))

        #with self.assertRaises(SBtab.SBtabError):
        #    random_sbtab.validate_extension(test=ic)
        
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
