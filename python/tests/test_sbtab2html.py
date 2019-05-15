#!/usr/bin/env python
import unittest
import sys
import os
import copy

sys.path.insert(0,os.path.join(os.path.dirname(__file__), '..'))
import SBtab
import misc

class TestSBtabConversionToHTML(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        self.table_names = [f for f in os.listdir('python/tests/tables/') if os.path.isfile(os.path.join('python/tests/tables/', f))]
        self.doc_names = [f for f in os.listdir('python/tests/docs/') if os.path.isfile(os.path.join('python/tests/docs/', f))]

        self.sbtabs = []        
        self.sbtab_docs = []

        for i, t in enumerate(self.table_names):
            if t.startswith('_'): continue
            p = open('python/tests/tables/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

        for i, d in enumerate(self.doc_names):
            if d.startswith('_'): continue
            p = open('python/tests/docs/' + d, 'r')
            p_content = p.read()
            sbtab_doc = SBtab.SBtabDocument('test_'+str(i),sbtab_init=p_content, filename=d)
            self.sbtab_docs.append(sbtab_doc)
            p.close()

    def test_single_tab_conversion(self):
        '''
        test if normal SBtab tables can be converted to valid HTML files
        '''
        for i, sbtab in enumerate(self.sbtabs):
            html_string = misc.sbtab_to_html(sbtab, self.table_names[i], 'standalone')
            self.assertEqual(html_string[0:5], '<html')
            self.assertEqual(html_string[-7:], '</html>')
            self.assertIn('<h2>%s</h2>' % (sbtab.filename), html_string)
            self.assertIn('!!SBtab', html_string)

    def test_multiple_tab_conversion(self):
        '''
        test if SBtab documents can be converted to valid but singular HTML files
        '''
        for i, sbtab in enumerate(self.sbtab_docs):
            html_string = misc.sbtab_to_html(sbtab, self.doc_names[i], 'standalone')
            self.assertEqual(html_string[0:5], '<html')
            self.assertEqual(html_string[-7:], '</html>')
            self.assertIn('<h2>%s</h2>' % (sbtab.filename), html_string)
            self.assertIn('!!SBtab', html_string)
            self.assertEqual(html_string.count('!!SBtab'), len(sbtab.sbtabs))

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
