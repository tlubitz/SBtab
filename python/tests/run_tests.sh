#!/bin/sh
echo "Start shell script from root: (./python/tests/run_tests.sh)"

python python/tests/test_sbtab.py
python python/tests/test_sbtab_doc.py
python python/tests/test_validator.py
python python/tests/test_sbtab2sbml.py
python python/tests/test_sbml2sbtab.py
python python/tests/test_misc.py
python python/tests/test_sbtab2html.py
