#!/usr/bin/env python
import unittest
import SBtab
import copy
      
            

class TestSBtabTable(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabTable class with files from test directory
        '''
        tables = ['teusink_compartment.csv',
                  'teusink_compound.csv',
                  'teusink_data.tsv',
                  'teusink_reaction.tsv']

        self.sbtabs = []
        for t in tables:
            p = open('tests/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

    def test_extension_validator(self):
        '''
        test if the extension is correct or not
        '''
        correct = ['test.tsv', 'test.csv', 'test.xls']
        incorrect = ['test.xlsx', 'test.xml', 'test.txt', 'test.rtf']

        random_sbtab = self.sbtabs[0]
        for c in correct:
            self.assertTrue(random_sbtab.validate_extension(test=c))

        for ic in incorrect:
            with self.assertRaises(SBtab.SBtabError):
                random_sbtab.validate_extension(test=ic)

            
    def test_columns_and_dict(self):
        '''
        test if columns and column dict hold the same columns
        '''
        for sbtab in self.sbtabs:
            self.assertEqual(sorted(sbtab.columns), sorted(sbtab.columns_dict.keys()))

    def test_change_value(self):
        '''
        function changes a value in the SBtab file
        change value receives (row_number, column_number, new_value)
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.change_value(1,1,'new_value'))
                       

    def test_change_value_by_name(self):
        '''
        function changes a value in the SBtab file by given row id and column name
        change value by name receives (row_id (=first column), column_name (!x), new_value)
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.change_value_by_name(sbtab.value_rows[0][0],
                                                       sbtab.columns[0], '2'))

    def test_create_list(self):
        '''
        function creates a list object of the SBtab contents
        [[header],[columns],[[row],[row],[row],[row]]]
        '''
        for sbtab in self.sbtabs:
            sbtab_list = sbtab.create_list()
            self.assertEqual(len(sbtab_list), 3)
            self.assertEqual(sbtab_list[0][0], sbtab.header_row)
            self.assertEqual(sbtab_list[1], sbtab.columns)
            self.assertEqual(sbtab_list[2], sbtab.value_rows)
            
    def test_add_row(self):
        '''
        function adds a row to the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.add_row(sbtab.value_rows[0]))
            self.assertTrue(sbtab.add_row(sbtab.value_rows[0], 4))
            with self.assertRaises(SBtab.SBtabError): sbtab.add_row(sbtab.value_rows[0], '4')
        
    def test_remove_row(self):
        '''
        function removes a row from the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.remove_row(1))
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_row('4')
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_row(5000)

    def test_add_column(self):
        '''
        function adds a column to the SBtab table
        '''
        for sbtab in self.sbtabs:
            test_column = ['X'] * (len(sbtab.value_rows) + 1)
            self.assertTrue(sbtab.add_column(test_column))
            self.assertTrue(sbtab.add_column(test_column, 0))
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[0])
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[:(len(test_column)-1)])
            with self.assertRaises(SBtab.SBtabError): sbtab.add_column(test_column[0], '4')
            
    def test_remove_row(self):
        '''
        function removes a column from the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.remove_column(1))
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_column('4')
            with self.assertRaises(SBtab.SBtabError): sbtab.remove_column(5000)

    def test_write_sbtab(self):
        '''
        function writes SBtab to hard drive
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.write(sbtab.filename))

            get_back = open(sbtab.filename, 'r')
            get_back_content = get_back.read()
            get_back_sbtab = SBtab.SBtabTable(get_back_content, sbtab.filename)
            get_back.close()

            self.assertEqual(sbtab.header_row.rstrip(), get_back_sbtab.header_row.rstrip())
            self.assertEqual(sbtab.columns, get_back_sbtab.columns)
            self.assertEqual(sbtab.value_rows, get_back_sbtab.value_rows)

    def test_transpose_table(self):
        '''
        function transposes the SBtab table
        '''
        for sbtab in self.sbtabs:
            self.assertTrue(sbtab.transpose_table())
            sbtab_transposed = copy.deepcopy(sbtab)
            sbtab_transposed.transpose_table()
            self.assertEqual((len(sbtab.value_rows) + 1),
                             len(sbtab_transposed.columns))
            self.assertEqual((len(sbtab_transposed.value_rows) + 1),
                             len(sbtab.columns))
        
    def tearDown(self):
        '''
        close file/s
        '''
        pass


class TestSBtabDocument(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtabDocument class with files from test directory
        '''
        docs = ['ecoli_ccm_aerobic_ProteinComposition_haverkorn_ECM_Model.tsv']

        self.sbtab_documents = []
        for d in docs:
            p = open('tests/' + t, 'r')
            p_content = p.read()
            sbtab = SBtab.SBtabTable(p_content, t)
            self.sbtabs.append(sbtab)
            p.close()

    def tearDown(self):
        '''
        tear down function
        '''
        pass

    
if __name__ == '__main__':
    unittest.main()
