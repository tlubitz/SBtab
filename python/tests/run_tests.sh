#!/bin/sh
python3 python/tests/test_sbtab.py
python3 test_sbtab_doc.py
python3 test_validator.py
python3 test_sbtab2sbml.py
python3 test_sbml2sbtab.py
