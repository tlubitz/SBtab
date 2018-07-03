#!/usr/bin/env python
import unittest
import SBtab
import copy


class TestSBtab(unittest.TestCase):

    def setUp(self):
        '''
        setup SBtab class with files from test directory
        '''
        files = ['teusink_compartment.csv','teusink_compound.csv','teusink_data.tsv','teusink_reaction.csv']
        self.p = open('tests/' + files[2], 'r')
        p_content = self.p.read()
        self.sbtab = SBtab.SBtabTable(p_content, files[2])
        
    def test_columns_and_dict(self):
        '''
        test if columns and column dict hold the same columns
        '''
        self.assertEqual(sorted(self.sbtab.columns), sorted(self.sbtab.columns_dict.keys()))

    def test_change_value(self):
        '''
        function changes a value in the SBtab file
        change value receives (row_number, column_number, new_value)
        '''
        self.assertTrue(self.sbtab.change_value(1,1,'new_value'))
                       

    def test_change_value_by_name(self):
        '''
        function changes a value in the SBtab file by given row id and column name
        change value by name receives (row_id (=first column), column_name (!x), new_value)
        '''
        self.assertTrue(self.sbtab.change_value_by_name(self.sbtab.value_rows[0][0],
                                                        self.sbtab.columns[0], '2'))

    def test_create_list(self):
        '''
        function creates a list object of the SBtab contents
        [[header],[columns],[[row],[row],[row],[row]]]
        '''
        sbtab_list = self.sbtab.create_list()
        self.assertEqual(len(sbtab_list), 3)
        self.assertEqual(sbtab_list[0][0], self.sbtab.header_row)
        self.assertEqual(sbtab_list[1], self.sbtab.columns)
        self.assertEqual(sbtab_list[2], self.sbtab.value_rows)

    def test_add_row(self):
        '''
        function adds a row to the SBtab table
        '''
        self.assertTrue(self.sbtab.add_row(self.sbtab.value_rows[0]))
        self.assertTrue(self.sbtab.add_row(self.sbtab.value_rows[0], 4))
        with self.assertRaises(SBtab.SBtabError): self.sbtab.add_row(self.sbtab.value_rows[0], '4')
        
    def test_remove_row(self):
        '''
        function removes a row from the SBtab table
        '''
        self.assertTrue(self.sbtab.remove_row(1))
        with self.assertRaises(SBtab.SBtabError): self.sbtab.remove_row('4')
        with self.assertRaises(SBtab.SBtabError): self.sbtab.remove_row(5000)

    def test_add_column(self):
        '''
        function adds a column to the SBtab table
        '''
        test_column = ['X'] * (len(self.sbtab.value_rows) + 1)
        self.assertTrue(self.sbtab.add_column(test_column))
        self.assertTrue(self.sbtab.add_column(test_column, 0))
        with self.assertRaises(SBtab.SBtabError): self.sbtab.add_column(test_column[0])
        with self.assertRaises(SBtab.SBtabError): self.sbtab.add_column(test_column[:(len(test_column)-1)])
        with self.assertRaises(SBtab.SBtabError): self.sbtab.add_column(test_column[0], '4')

    def test_remove_row(self):
        '''
        function removes a column from the SBtab table
        '''
        self.assertTrue(self.sbtab.remove_column(1))
        with self.assertRaises(SBtab.SBtabError): self.sbtab.remove_column('4')
        with self.assertRaises(SBtab.SBtabError): self.sbtab.remove_column(5000)

    def test_write_sbtab(self):
        '''
        function writes SBtab to hard drive
        '''
        test_name = 'test.tsv'
        self.assertTrue(self.sbtab.write(test_name))

        get_back = open(test_name, 'r')
        get_back_content = get_back.read()
        get_back_sbtab = SBtab.SBtabTable(get_back_content, test_name)
        get_back.close()

        self.assertEqual(self.sbtab.header_row, get_back_sbtab.header_row)
        self.assertEqual(self.sbtab.columns, get_back_sbtab.columns)
        self.assertEqual(self.sbtab.value_rows, get_back_sbtab.value_rows)

    def test_transpose_table(self):
        '''
        function transposes the SBtab table
        '''
        self.assertTrue(self.sbtab.transpose_table())
        sbtab_transposed = copy.deepcopy(self.sbtab)
        sbtab_transposed.transpose_table()
        self.assertEqual((len(self.sbtab.value_rows) + 1),
                         len(sbtab_transposed.columns))
        self.assertEqual((len(sbtab_transposed.value_rows) + 1),
                         len(self.sbtab.columns))
        
    def tearDown(self):
        '''
        close file/s
        '''
        self.p.close()

        
if __name__ == '__main__':
    unittest.main()
