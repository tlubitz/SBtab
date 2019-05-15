#!/bin/sh
echo "Start shell script from root: (./python/tests/run_tests.sh)"

python3.5 python/tests/test_sbtab.py
python3.5 python/tests/test_sbtab_doc.py
python3.5 python/tests/test_validator.py
python3.5 python/tests/test_sbtab2sbml.py
python3.5 python/tests/test_sbml2sbtab.py
python3.5 python/tests/test_misc.py
python3.5 python/tests/test_sbtab2html.py
