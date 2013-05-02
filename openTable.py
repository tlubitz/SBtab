#!/usr/bin/python

import tablibIO


def getTable(fpath):
    '''
    Read table with tablib and returns tablib dataset
    Input file in csv, tsv, ods or xls format
    '''

    dataset = tablibIO.importSet(fpath)
    return dataset
