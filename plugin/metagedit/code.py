
# =============================================================================================
# This program is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either version
# 3 of the License, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# This script must/should come together with a copy of the GNU General Public License. If not,
# access <http://www.gnu.org/licenses/> to find and read it.
#
# Author: Pedro Vernetti G.
# Name: Metagedit
# Description: gedit plugin which adds multiple improvements and functionalities to it
#
# #  In order to have this script working (if it is currently not), run 'install.sh'.
# =============================================================================================

import re
from gi.repository import Gio


_geditSettings = Gio.Settings.new(r'org.gnome.gedit.preferences.editor')

def defaultIndentation():
    if (_geditSettings.get_value(r'insert-spaces').get_boolean()):
        return (r' ' * _geditSettings.get_value(r'tabs-size').get_uint32())
    return '\t'



_l_ABAP                 = r'abap' # missing from Gedit
_l_ABNF                 = r'abnf'
_l_ActionScript         = r'actionscript'
_l_Ada                  = r'ada'
_l_ANSForth94           = r'ansforth94'
_l_APL                  = r'apl' # missing from Gedit
_l_AppleScript          = r'applescript' # missing from Gedit
_l_ASCIIDoc             = r'asciidoc'
_l_ASP                  = r'asp'
_l_Automake             = r'automake'
_l_AWK                  = r'awk'
_l_Batch                = r'dosbatch'
_l_BennuGD              = r'bennugd'
_l_BluespecVerilog      = r'bluespecsystemverilog'
_l_Boo                  = r'boo'
_l_C                    = r'c'
_l_CGShader             = r'cgshaderlanguage'
_l_Clojure              = r'clojure' # missing from Gedit
_l_CObjCHeader          = r'c/objcheader'
_l_COBOL                = r'cobol'
_l_Cobra                = r'cobra' # missing from Gedit
_l_CoffeeScript         = r'coffeescript' # missing from Gedit
_l_ColdFusion           = r'coldfusion' # missing from Gedit
_l_Cpp                  = r'cpp'
_l_Csharp               = r'csharp'
_l_CSS                  = r'css'
_l_CUDA                 = r'cuda'
_l_Cypher               = r'cypher' # missing from Gedit
_l_D                    = r'd'
_l_Dart                 = r'dart'
_l_Delphi               = r'delphi' # missing from Gedit
_l_Desktop              = r'desktop'
_l_DocBook              = r'docbook'
_l_Dockerfile           = r'dockerfile'
_l_Dot                  = r'graphvizdot'
_l_DTD                  = r'dtd'
_l_dtl                  = r'djangotemplate'
_l_Eiffel               = r'eiffel'
_l_Elixir               = r'elixir' # missing from Gedit
_l_Erlang               = r'erlang'
_l_Euphoria             = r'euphoria' # missing from Gedit
_l_FCL                  = r'fcl'
_l_Fish                 = r'fish'
_l_Fluent               = r'fluent'
_l_Forth                = r'forth'
_l_FORTRAN77            = r'fortran77' # missing from Gedit
_l_FORTRAN95            = r'fortran95'
_l_Fsharp               = r'fsharp'
_l_GAP                  = r'gap'
_l_GDBScript            = r'gdbscript'
_l_Genie                = r'genie'
_l_gettextTranslation   = r'gettexttranslation'
_l_Go                   = r'go'
_l_Gradle               = r'gradle'
_l_Groovy               = r'groovy'
_l_GTKRC                = r'gtkrc'
_l_Haskell              = r'haskell'
_l_Haxe                 = r'haxe'
_l_Hpp                  = r'cppheader'
_l_HTML                 = r'html'
_l_Icon                 = r'icon' # missing from Gedit
_l_IDL                  = r'idl'
_l_IDLGDL               = r'idl/pvwave/gdl'
_l_ImageJ               = r'imagej'
_l_ini                  = r'ini'
_l_J                    = r'j'
_l_Jade                 = r'jade'
_l_Java                 = r'java'
_l_JavaScript           = r'javascript'
_l_JSX                  = r'jsx'
_l_Julia                = r'julia'
_l_K                    = r'k' # missing from Gedit
_l_Kotlin               = r'kotlin'
_l_LaTeX                = r'latex'
_l_Less                 = r'less'
_l_Lex                  = r'lex'
_l_libtool              = r'libtool'
_l_LISP                 = r'commonlisp'
_l_LiterateHaskell      = r'literatehaskell'
_l_LLVM                 = r'llvmir'
_l_logcat               = r'logcat'
_l_Logtalk              = r'logtalk'
_l_Lua                  = r'lua'
_l_m4                   = r'm4'
_l_Make                 = r'cmake'
_l_Makefile             = r'makefile'
_l_Mallard              = r'mallard'
_l_Markdown             = r'markdown'
_l_Mathematica          = r'mathematica' # missing from Gedit
_l_MATLAB               = r'matlab'
_l_Maxima               = r'maxima'
_l_MediaWiki            = r'madiawiki'
_l_Meson                = r'meson'
_l_Modelica             = r'modelica'
_l_MXML                 = r'mxml'
_l_Nemerle              = r'nemerle'
_l_NetRexx              = r'netrexx'
_l_Nim                  = r'nim' # missing from Gedit
_l_NSIS                 = r'nsis'
_l_ObjC                 = r'objc'
_l_ObjJ                 = r'objj'
_l_OCaml                = r'ocaml'
_l_occam                = r'occam' # missing from Gedit
_l_OCL                  = r'ocl'
_l_Octave               = r'octave'
_l_OOC                  = r'ooc'
_l_Opal                 = r'opal'
_l_OpenCL               = r'opencl'
_l_OpenGLShading        = r'openglshadinglanguage'
_l_Pascal               = r'pascal'
_l_Perl                 = r'perl'
_l_PHP                  = r'php'
_l_Pig                  = r'pig'
_l_pkgconfig            = r'pkgconfig'
_l_PowerShell           = r'powershell'
_l_Prolog               = r'prolog'
_l_Protobuf             = r'protobuf'
_l_Puppet               = r'puppet'
_l_Python3              = r'python3'
_l_Python               = r'python'
_l_R                    = r'r'
_l_Raku                 = r'raku' # missing from Gedit
_l_Red                  = r'red' # missing from Gedit
_l_reStructuredText     = r'restructuredtext'
_l_RPMspec              = r'rpmspec'
_l_Ruby                 = r'ruby'
_l_Rust                 = r'rust'
_l_Scala                = r'scala'
_l_Scheme               = r'scheme'
_l_Scilab               = r'scilab'
_l_SCSS                 = r'scss'
_l_Shell                = r'sh'
_l_Simula               = r'simula' # missing from Gedit
_l_Smalltalk            = r'smalltalk' # missing from Gedit
_l_Smarty               = r'smartytemplate' # missing from Gedit
_l_SML                  = r'standardml'
_l_Solidity             = r'solidity'
_l_SPARK                = r'spark' # missing from Gedit
_l_SPARQL               = r'sparql'
_l_SQL                  = r'sql'
_l_Sweave               = r'sweave'
_l_Swift                = r'swift'
_l_SystemVerilog        = r'systemverilog'
_l_Tcl                  = r'tcl'
_l_Tera                 = r'teratemplate'
_l_TexInfo              = r'texinfo'
_l_Thrift               = r'thrift'
_l_TOML                 = r'toml'
_l_txt2tags             = r'txt2tags'
_l_TypeScript           = r'typescript'
_l_TypeScriptJSX        = r'typescriptjsx'
_l_Vala                 = r'vala'
_l_VBNET                = r'vbnet'
_l_Verilog              = r'verilog'
_l_VHDL                 = r'vhdl'
_l_XML                  = r'xml'
_l_XSLT                 = r'xslt'
_l_Yacc                 = r'yacc'
_l_YAML                 = r'yaml'

def cleanLanguageName( name ):
    name = name.casefold().replace(r'+', r'p').replace(r'#', r'sharp')
    name = name.replace(r'objective', r'obj').replace(r'common', r'')
    return re.sub(r'[\s._-]+', r'', re.sub(r'\([^)]*\)', r'', name))



## COMMENT/UNCOMMENT

_asmComment      = r';'
_cppComment      = r'//'
_shComment       = r'#'
_sqlComment      = r'--'
_texComment      = r'%'
_vbComment       = '\x27'

_cComment        = (r'/*', r'*/')
_lispComment     = (r'#|', r'|#')
_matlabComment   = (r'%{', r'%}')
_pascalComment   = (r'(*', r'*)')
_templateComment = (r'{#', r'#}')
_xmlComment      = (r'<!--', r'-->')

commentSymbol = {
    r'special' : {_l_COBOL, _l_FORTRAN77, _l_reStructuredText},
    r'line'    : {_l_ABNF:_asmComment, _l_ActionScript:_cppComment, _l_Ada:_sqlComment,
                  _l_ANSForth94:'\\', _l_ASCIIDoc:_cppComment, _l_ASP:_vbComment,
                  _l_Automake:_shComment, _l_AWK:_shComment, _l_BennuGD:_cppComment,
                  _l_BluespecVerilog:_cppComment, _l_Boo:_cppComment, _l_C:_cppComment,
                  _l_Csharp:_cppComment, _l_Cpp:_cppComment, _l_CGShader:_cppComment,
                  _l_Hpp:_cppComment, _l_Make:_shComment, _l_CObjCHeader:_cppComment,
                  _l_LISP:_asmComment, _l_CUDA:_cppComment, _l_D:_cppComment, _l_Dart:_cppComment,
                  _l_Desktop:_shComment, _l_Dockerfile:_shComment, _l_Eiffel:_sqlComment,
                  _l_Erlang:_texComment, _l_Fsharp:_cppComment, _l_FCL:_cppComment,
                  _l_Fish:_shComment, _l_Fluent:_shComment, _l_Forth:'\\', _l_FORTRAN95:r'!',
                  _l_GAP:_shComment, _l_GDBScript:_shComment, _l_Genie:_cppComment,
                  _l_gettextTranslation:_shComment, _l_Go:_cppComment, _l_Gradle:_cppComment,
                  _l_Dot:_cppComment, _l_Groovy:_cppComment, _l_GTKRC:_shComment,
                  _l_Haskell:_sqlComment, _l_LiterateHaskell:_sqlComment, _l_Haxe:_cppComment,
                  _l_IDL:_cppComment, _l_IDLGDL:_asmComment, _l_ImageJ:_cppComment,
                  _l_ini:_asmComment, _l_J:r'NB.', _l_Jade:r'//-', _l_Java:_cppComment,
                  _l_JavaScript:_cppComment, _l_JSX:_cppComment, _l_Julia:_shComment,
                  _l_Kotlin:_cppComment, _l_LaTeX:_texComment, _l_Less:_cppComment,
                  _l_Lex:_cppComment, _l_libtool:_shComment, _l_LLVM:_asmComment,
                  _l_Logtalk:_texComment, _l_Lua:_sqlComment, _l_m4:_shComment, _l_Makefile:_shComment,
                  _l_MATLAB:_texComment, _l_Meson:_shComment, _l_Modelica:_cppComment,
                  _l_Nemerle:_cppComment, _l_NetRexx:_sqlComment, _l_NSIS:_asmComment,
                  _l_ObjC:_cppComment, _l_ObjJ:_cppComment, _l_OCL:_sqlComment, _l_Octave:_texComment,
                  _l_OOC:_cppComment, _l_Opal:_sqlComment, _l_OpenCL:_cppComment,
                  _l_OpenGLShading:_cppComment, _l_Pascal:_cppComment, _l_Perl:_shComment,
                  _l_PHP:_cppComment, _l_Pig:_sqlComment, _l_pkgconfig:_shComment,
                  _l_PowerShell:_shComment, _l_Prolog:_texComment, _l_Protobuf:_cppComment,
                  _l_Puppet:_shComment, _l_Python:_shComment, _l_Python3:_shComment, _l_R:_shComment,
                  _l_RPMspec:_shComment, _l_Ruby:_shComment, _l_Rust:_cppComment,
                  _l_Scala:_cppComment, _l_Scheme:_asmComment, _l_Scilab:_cppComment,
                  _l_SCSS:_cppComment, _l_Shell:_shComment, _l_Solidity:_cppComment,
                  _l_SPARQL:_shComment, _l_SQL:_sqlComment, _l_Sweave:_texComment,
                  _l_Swift:_cppComment, _l_SystemVerilog:_cppComment, _l_Tcl:_shComment,
                  _l_TexInfo:r'@c', _l_Thrift:_cppComment, _l_TOML:_shComment,
                  _l_txt2tags:_texComment, _l_TypeScript:_cppComment, _l_TypeScriptJSX:_cppComment,
                  _l_Vala:_cppComment, _l_VBNET:_vbComment, _l_Verilog:_cppComment,
                  _l_VHDL:_sqlComment, _l_Yacc:_cppComment, _l_YAML:_shComment,
                  _l_CoffeeScript:_shComment, _l_Delphi:_cppComment, _l_Cypher:_cppComment,
                  _l_FORTRAN77:r'C', _l_COBOL:r'*', _l_Raku:_shComment, _l_Cobra:_shComment,
                  _l_APL:'\u235d', _l_AppleScript:_sqlComment, _l_Clojure:_asmComment,
                  _l_Elixir:_shComment, _l_Icon:_shComment, _l_K:r'/', _l_logcat:r'---------',
                  _l_Nim:_shComment, _l_ABAP:'\x22', _l_Euphoria:_sqlComment, _l_occam:_sqlComment,
                  _l_SPARK:_sqlComment, _l_Red:_asmComment, _l_Batch:r'rem'}, #TODO: dosbatch case
    r'line#'   : {_l_Boo, _l_ini, _l_Octave, _l_PHP, _l_Thrift},
    r'block'   : {_l_ActionScript:_cComment, _l_ANSForth94:_pascalComment, _l_BennuGD:_cComment,
                  _l_BluespecVerilog:_cComment, _l_Boo:_cComment, _l_C:_cComment,
                  _l_Csharp:_cComment, _l_Cpp:_cComment, _l_CGShader:_cComment, _l_Hpp:_cComment,
                  _l_Make:(r'#[[', r']]'), _l_CObjCHeader:_cComment, _l_LISP:_lispComment,
                  _l_CSS:_cComment, _l_CUDA:_cComment, _l_D:_cComment, _l_Dart:_cComment,
                  _l_dtl:_templateComment, _l_DocBook:_xmlComment, _l_DTD:_xmlComment,
                  _l_Fsharp:_pascalComment, _l_Forth:_pascalComment, _l_Genie:_cComment,
                  _l_Go:_cComment, _l_Gradle:_cComment, _l_Dot:_cComment, _l_Groovy:_cComment,
                  _l_Haskell:(r'{-', r'-}'), _l_LiterateHaskell:(r'{-', r'-}'),
                  _l_Haxe:_cComment, _l_HTML:_xmlComment, _l_IDL:_cComment, _l_ImageJ:_cComment,
                  _l_Java:_cComment, _l_JavaScript:_cComment, _l_JSX:_cComment,
                  _l_Julia:(r'#=', r'=#'), _l_Kotlin:_cComment, _l_Less:_cComment, _l_Lex:_cComment,
                  _l_Logtalk:_cComment, _l_Lua:(r'--[[', r']]'), _l_Mallard:_xmlComment,
                  _l_MATLAB:_matlabComment, _l_Maxima:_cComment, _l_MediaWiki:_xmlComment,
                  _l_Modelica:_cComment, _l_MXML:_xmlComment, _l_Nemerle:_cComment,
                  _l_Markdown:_xmlComment, _l_NetRexx:_cComment, _l_ObjC:_cComment, _l_ObjJ:_cComment,
                  _l_OCaml:_pascalComment, _l_Octave:_matlabComment, _l_OOC:_cComment,
                  _l_Opal:_cComment, _l_OpenCL:_cComment, _l_OpenGLShading:_cComment,
                  _l_Pascal:_pascalComment, _l_PHP:_cComment, _l_Pig:_cComment,
                  _l_PowerShell:(r'<#', r'#>'), _l_Prolog:_cComment, _l_Protobuf:_cComment,
                  _l_reStructuredText:(), _l_Rust:_cComment, _l_Scala:_cComment,
                  _l_Scheme:_lispComment, _l_SCSS:_cComment, _l_Solidity:_cComment,
                  _l_SML:_pascalComment, _l_Swift:_cComment, _l_SystemVerilog:_cComment,
                  _l_Tera:_templateComment, _l_Thrift:_cComment, _l_TypeScript:_cComment,
                  _l_TypeScriptJSX:_cComment, _l_Vala:_cComment, _l_Verilog:_cComment,
                  _l_XML:_xmlComment, _l_XSLT:_xmlComment, _l_Yacc:_cComment,
                  _l_Delphi:_pascalComment, _l_Smalltalk:('\x22', '\x22'),
                  _l_ColdFusion:(r'<!---', r'--->'), _l_Cobra:(r'/#', r'#/'),
                  _l_Mathematica:_pascalComment, _l_Smarty:(r'{*', r'*}'), _l_Nim:(r'#[', r']#'),
                  _l_AppleScript:_pascalComment, _l_Clojure:(r'(comment', r')'),
                  _l_Simula:(r'comment', r';')}} #TODO: simula case
