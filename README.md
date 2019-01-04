SBtab - Table format for Systems Biology
========================================
Python code and example files by
<b>Timo Lubitz, Jens Hahn, Elad Noor, Frank Bergmann (2018)</b>.

Data tables in the form of spreadsheets or delimited text files are the most utilised data format in Systems Biology. However, they are often not sufficiently structured and lack clear naming conventions
that would be required for modelling. We propose the <b>SBtab</b> format as an attempt to establish an
easy-to-use table format that is both flexible and clearly structured. It comprises defined table types
for different kinds of data; syntax rules for usage of names, shortnames, and database identifiers used
for annotation; and standardised formulae for reaction stoichiometries. Predefined table types can be
used to define biochemical network models and the biochemical constants therein. The user can also
define own table types, adjusting SBtab to other types of data.

The SBtab specification can be found on the [SBtab homepage](https://www.sbtab.net/sbtab/default/downloads.html#spec). The homepage also provides various information on example files, frequently asked questions, online tools, and tutorials.

---

SBtab comes along with software tools which can be employed in 3 different ways:

<ol>
<li><b>In the online interface or as home server version</b><br>
  You can use the software tools that come with SBtab in the convenient online interface
  on https://www.sbtab.net. The page is built with the Python web framework web2py.
  
  If you want to run
  the web2py application on your own home server, you can download it from this
  repository's directory SBtab/python/web_version. Change to this directory to find more information
  on the usage.
  ![SBtab online](https://github.com/tlubitz/SBtab/sbtab_screen.png)
  </li>

<li><b>As a Python3 package (pip installer)</b><br>
  The tools can be employed as a Python3 package. It needs to be installed via
  [pypi](https://pypi.org/project/sbtab/). Please type on your commandline<br><br>
    
  > sudo pip3 install sbtab
  
  You will then be able to import the SBtab library into your Python3 modules by adding
  
  > import sbtab
  
  to them. See the code examples in this repository's directory SBtab/python. Also, you
  will find further information on the usage in the [SBtab specification](https://www.sbtab.net/sbtab/default/downloads.html#spec).
  
  **Please note that the directory SBtab/pypi_installer only holds the files for the
  pip installer build up and is not required at all for users that want to
  employ SBtab.**
  </li>
  
<li><b>From the commandline (for experienced users)</b><br>
  You can employ the SBtab commandline tools from the directory
  SBtab/python. To use this option,
  you will have to install the required packages on your own and put
  the Python modules to their according directory. Details on the usage
  of the commandline tools you can find in the directory SBtab/python.
</li>
</ol>

---

The SBtab repository consists of the following directories and contents:

<b>R</b><br>
SBtab interface for the language [R](https://www.r-project.org/). See directory for details on the usage.

<b>definition table:</b><br>
Default definitions of predefined SBtab table types.

<b>excel:</b><br>
Windows installer and source code for the excel add-in (courtesy of Frank T. Bergmann). Works for SBtab version 1.0 and the .xls format.

<b>sbtab examples:</b><br>
Example SBtab files. These files can also be found including explanatory words in the [online SBtab Download Section](https://www.sbtab.net/sbtab/default/downloads.html)

<b>python:</b>
<ul>
<li>Source scripts and commandline Python3 modules, including a file and object validator, and a converter to and from SBML.</li>

<li><b>Documentation:</b><br>
HTML pydoc documentation of the SBtab interface and source code.</li>

<li><b>SQLite interface:</b><br>
Python interface for querying SQLite databases via SBtab (courtesy of Elad Noor).</li>

<li><b>web2py:</b><br>
[Web2py](http://www.web2py.com) server files for the SBtab online tools. Can be run locally and offline if required.</li>
</ul>
