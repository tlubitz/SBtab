from . import misc
from . import sbml2sbtab
from . import sbtab2sbml
from . import sbtab2html
from . import SBtab
from . import validatorSBtab

from importlib import resources
__version__ = resources.files(__name__).joinpath("VERSION").read_text(
    encoding="utf-8").strip()
