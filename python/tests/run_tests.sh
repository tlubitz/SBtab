#!/bin/sh
echo "Start shell script from root: (./python/tests/run_tests.sh)"

echo "Test SBtab"
python3 python/tests/test_sbtab.py

echo "Test SBtab Doc"
python3 python/tests/test_sbtab_doc.py

echo "Test Validator"
python3 python/tests/test_validator.py

echo "Test SBtab2SBML"
python3 python/tests/test_sbtab2sbml.py

echo "Test SBML2SBtab"
python3 python/tests/test_sbml2sbtab.py

echo "Test Misc"
python3 python/tests/test_misc.py

echo "Test sbtab2html"
python3 python/tests/test_sbtab2html.py
