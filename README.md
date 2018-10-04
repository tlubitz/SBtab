SBtab - Table format for Systems Biology
========================================
Python code and example files by
<b>Timo Lubitz, Jens Hahn, Elad Noor, Frank Bergmann (2018)</b>.

Welcome to the SBtab respository. In short, SBtab is a table format for
Systems Biology. Its specification can be found on the [SBtab homepage](https://www.sbtab.net/sbtab/default/specification.html). SBtab comes
along with software tools which can be employed
in 3 different ways:

---

<ol>
<li><b>In the online interface</b><br>
  You can use the software tools that come with SBtab in the convenient online interface
  on https://www.sbtab.net. The page is built with the Python web framework web2py. If you want to run
  the web2py application on your own home server, you can download it from this
  repository's directory SBtab/python/web_version.
  </li>

<li><b>As a Python3 package (pip installer)</b><br>
  The tools can be employed as a Python3 package. It needs to be installed via
  pypi. Please type on your commandline <br>
  
  > sudo pip3 install sbtab
  
  You will then be able to import sbtab into your Python3 modules by adding
  
  > import sbtab
  
  to them. See the specification for detailed usage of this package. You will
  also find information in the repository directory SBtab/python/. **Please
  note that the directory SBtab/pypi_installer only holds the files for the
  pip installer build up and is not required at all for users that want to
  employ SBtab.**
  </li>
  
<li><b>From the command line (for experienced users)</b><br>
  You can employ the command line tools which you find in the directory
  SBtab/python. To use this option,
  you will have to install the required packages on your own and put
  the Python modules to their according directory. Details on the usage
  of the command line tools you can find in the directory SBtab/python.
</li>
</ol>

---

The directories and their contents are:

<b>definition table:</b><br>
Default definitions of predefined SBtab table types.

<b>excel:</b><br>
windows installer and source code for the excel add-in (copyright Frank T. Bergmann).

<b>sbtab examples:</b><br>
example SBtab files.

<b>python:</b>
<ul>
<li>source scripts and command line python modules, including validator and converter to and from SBML (copyright Timo Lubitz).</li>

<li><b>documentation:</b><br>
HTML documentation of the SBtab repository and source code (copyright Timo Lubitz & Jens Hahn).</li>

<li><b>sqlite interface:</b><br>
Python interface for querying SQLite database via SBtab (copyright Elad Noor).</li>

<li><b>web2py:</b><br>
Web2py server files for the SBtab online tools. Can be run locally and offline if required (copyright Massimo Di Pierro (web2py) and Timo Lubitz (SBtab application))</li>
</ul>
