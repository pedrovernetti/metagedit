
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
from codecs import lookup as codecLookup
from random import shuffle
from unicodedata import normalize as unicodeNormalize, combining as unicodeCombining
from urllib.parse import quote as urlquote, unquote as urlunquote
from html.entities import codepoint2name as codepoint2html, name2codepoint as html2codepoint
from chardet import detect as detectEncoding
try:
    from googletrans import Translator, LANGUAGES as translatorLANGUAGES
    from textwrap import wrap as textWrap
    translationIsAvailable = True
except:
    translationIsAvailable = False

from .code import *



_emptyLine = re.compile(r'^\s*$')



def getSelection( document, noSelectionMeansEverything=True ):
    if (not document.get_has_selection()):
        if (noSelectionMeansEverything): # get whole document
            return (document.get_start_iter(), document.get_end_iter(), True)
        else: # get current character
            beg = document.get_iter_at_mark(document.get_insert())
            end = document.get_iter_at_mark(document.get_insert())
            end.forward_char()
            return (beg, end, True)
    beg, end = document.get_selection_bounds()
    return (beg, end, False)



def getSelectedLines( document, noSelectionMeansEverything=True ):
    if (not document.get_has_selection()):
        if (noSelectionMeansEverything): # get whole document
            beg, end = (document.get_start_iter(), document.get_end_iter())
            return (beg, end, True)
        else: # get current line
            line = document.get_iter_at_mark(document.get_insert()).get_line()
            end = document.get_iter_at_line(line)
            end.forward_line()
            return (document.get_iter_at_line(line), end, True)
    beg, end = document.get_selection_bounds()
    if (beg.ends_line()): beg.forward_line()
    elif (not beg.starts_line()): beg.set_line_offset(0)
    if (end.starts_line()): end.backward_char()
    elif (not end.ends_line()): end.forward_to_line_end()
    return (beg, end, False)



def removeTrailingSpaces( document, onSaveMode=False ):
    ## REMOVE TRAILING SPACES
    trailingSpaces = re.compile(r'[\f\t \u2000-\u200A\u205F\u3000]+$')
    if (onSaveMode):
        beg, end, noneSelected = (document.get_start_iter(), document.get_end_iter(), True)
    else:
        beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False)
    document.begin_user_action()
    if (noneSelected): # whole-document mode (doesn't move the cursor)
        lineNumber = 0
        for line in selection.splitlines():
            if (len(line) != 0):
                beg.set_line(lineNumber)
                beg.set_line_offset(len(trailingSpaces.sub(r'', line)))
                end.set_line(lineNumber)
                end.set_line_offset(len(line))
                document.delete(beg, end)
            lineNumber += 1
        removeTrailingNewlines(document)
    else: # selection mode
        selection = trailingSpaces.sub(r'', selection, flags=re.MULTILINE)
        document.delete(beg, end)
        document.insert_at_cursor(selection)
    document.end_user_action()


def removeTrailingNewlines( document ):
    ## REMOVE TRAILING SPACES
    end = document.get_end_iter()
    if (end.starts_line()):
        while (end.backward_char()):
            if (not end.ends_line()):
                  end.forward_to_line_end()
                  break
    document.delete(end, document.get_end_iter())
    #document.insert(end, "\n") # uncomment to always leave 1 trailing newline



def removeEmptyLines( document ): #TODO: selection mode inserts trailing newlines for some reason - deleting everything
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    document.begin_user_action()
    if (noneSelected): # whole-document mode (doesn't move the cursor)
        for lineNumber in reversed(range(0, (document.get_line_count() - 1))):
            beg.set_line(lineNumber)
            end.set_line(lineNumber)
            if (not end.ends_line()): end.forward_to_line_end()
            if (_emptyLine.match(document.get_text(beg, end, False))):
                end.forward_char()
                document.delete(beg, end)
        removeTrailingNewlines(document)
    else: # selection mode
        beg.backward_char()
        selection = document.get_text(beg, end, False)
        if (_emptyLine.match(selection, flags=re.MULTILINE)): selection = r''
        selection = re.sub(r'\n\s*\n', r'\n', selection, flags=re.MULTILINE)
        document.delete(beg, end)
        document.insert_at_cursor(selection)
    document.end_user_action()



def removeLines( document ):
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document, False)
    if (not noneSelected): beg.backward_char()
    document.begin_user_action()
    document.delete(beg, end)
    document.end_user_action()



def joinLines( document, separatedWithSpaces=True ):
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False)
    selection = re.sub(r'\n\s*\n', r'\n', selection, flags=re.MULTILINE).strip()
    selection = selection.replace('\n', (r' ' if separatedWithSpaces else r''))
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor(selection)
    document.end_user_action()



def reverseLines( document ):
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    if (noneSelected):
        cursorPosition = document.get_iter_at_mark(document.get_insert())
        line = document.get_line_count() - (cursorPosition.get_line() + 1)
        column = cursorPosition.get_line_offset()
    selection = document.get_text(beg, end, False).splitlines()
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor('\n'.join(reversed(selection)))
    if (noneSelected):
        document.place_cursor(document.get_iter_at_line_offset(line, column))
    document.end_user_action()



def _dedupedLines( selection, caseSensitive=True, KeepEmptyOnes=False, offset=0 ):
    ## LINE OPERATIONS
    emptyLine = re.compile(r'^\s*$')
    finalContent = []
    seen = set()
    for line in selection:
        line_ = line[offset:] if caseSensitive else line[offset:].casefold()
        if (line_ not in seen):
            finalContent.append(line)
            if (not (KeepEmptyOnes and emptyLine.match(line_))): seen.add(line_)
    return finalContent

def dedupLines( document, caseSensitive=False, KeepEmptyOnes=False, offset=0 ):
    ## LINE OPERATIONS
    emptyLine = re.compile(r'^\s*$')
    beg, end, noneSelected = getSelectedLines(document)
    document.begin_user_action()
    if (noneSelected): # whole-document mode (doesn't move the cursor)
        seen = set()
        for lineNumber in reversed(range(0, document.get_line_count())):
            beg.set_line(lineNumber)
            end.set_line(lineNumber)
            if (not end.ends_line()): end.forward_to_line_end()
            line = document.get_text(beg, end, False)[offset:]
            if (not caseSensitive): line = line.casefold()
            if ((not (KeepEmptyOnes and emptyLine.match(line))) and
                ((line in seen) or seen.add(line))):
                end.forward_char()
                document.delete(beg, end)
    else: # selection mode
        selection = document.get_text(beg, end, False).splitlines()
        document.delete(beg, end)
        selection = _dedupedLines(selection, caseSensitive, KeepEmptyOnes, offset)
        document.insert_at_cursor('\n'.join(selection))
    document.end_user_action()



def shuffleLines( document, dedup=False, caseSensitive=False, offset=0 ):
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False).splitlines()
    if (dedup): selection = _dedupedLines(selection, caseSensitive, offset)
    shuffle(selection)
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor('\n'.join(selection))
    document.end_user_action()



def sortLines( document, reverse=False, dedup=False, caseSensitive=False, offset=0 ):
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False).splitlines()
    if (dedup): selection = _dedupedLines(selection, caseSensitive, offset)
    if (not caseSensitive):
        sortKey = lambda x: re.sub(r'\s+', r'', x[offset:].casefold())
    else:
        sortKey = lambda x: re.sub(r'\s+', r'', x[offset:])
    selection = sorted(selection, key=sortKey)
    if (reverse): selection = reversed(selection)
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor('\n'.join(selection))
    document.end_user_action()



def _commentedSpecialCaseLine( line, language, cursorOffset ):
    ## COMMENT/UNCOMMENT
    if ((language == r'cobol') and (line[6] != r'*')):
        line = (line[:6], line[6:])
        if (line[1].startswith(r' ')):
            if (cursorOffset >= len(line[0])): cursorOffset += 1
            return ((line[0] + r'*' + line[1]), cursorOffset)
        else:
            if (cursorOffset >= len(line[0])): cursorOffset += 2
            return ((line[0] + r'* ' + line[1]), cursorOffset)
    elif((language == r'fortran77') and (not line.startswith(r'C'))):
        if (line.startswith(r' ')): return ((r'C' + line), (cursorOffset + 1))
        return ((r'C ' + line), (cursorOffset + 2))
    return (line, cursorOffset)

def _commentedLine( line, language, preferHashComment=False, cursorOffset=0 ):
    ## COMMENT/UNCOMMENT
    if (len(line) > 3): line = [line[0], line[-2], line[-1]]
    if (len(line[1]) == 0): return (''.join(line), cursorOffset)
    space = r' ' if not line[1].startswith(r' ') else r''
    indentationLength = len(line[0])
    if (language in commentSymbol[r'line']):
        hasAltHashComment = language in commentSymbol[r'line#']
        startOfComment = commentSymbol[r'line'][language]
        if (hasAltHashComment):
            if (preferHashComment): startOfComment = r'#'
            possibleStartsOfComment = (commentSymbol[r'line'][language], r'#')
        else:
            possibleStartsOfComment = (startOfComment)
        if (line[1].startswith(possibleStartsOfComment)):
            return (r''.join(line), cursorOffset)
        if (cursorOffset >= indentationLength):
            cursorOffset += (len(startOfComment) + len(space))
        line = line[0] + startOfComment + space + line[1] + line[2]
    elif (language in commentSymbol[r'block']):
        limits = commentSymbol[r'block'][language]
        if (line[1].startswith(limits[0])): return (r''.join(line), cursorOffset)
        if (cursorOffset >= indentationLength):
            if (cursorOffset >= (indentationLength + len(line[1]))):
                cursorOffset += (1 + len(limits[1]))
            cursorOffset += (len(limits[0]) + len(space))
        line = line[0] + limits[0] + space + line[1] + r' ' + limits[1] + line[2]
    else:
        line = r''.join(line)
        if (language in commentSymbol[r'special']):
            return _commentedSpecialCaseLine(line, language, cursorOffset)
    return (line, cursorOffset)

def commentLines( document ):
    ## COMMENT/UNCOMMENT
    beg, end, noneSelected = getSelectedLines(document, False)
    selection = document.get_text(beg, end, False)
    if (noneSelected and _emptyLine.match(selection)): return
    language = cleanLanguageName(document.get_language().get_name())
    lineParts = re.compile(r'^([\t ]*)(.*?)(\s*)$')
    document.begin_user_action()
    document.delete(beg, end)
    if (noneSelected):
        line = document.get_iter_at_mark(document.get_insert())
        column = line.get_line_offset()
        line = line.get_line()
        selection = lineParts.search(selection).groups()
        selection = [(r'' if part is None else part) for part in selection]
        selection, column = _commentedLine(selection, language, False, column) #TODO: preferHash~
        document.insert_at_cursor(selection)
        document.place_cursor(document.get_iter_at_line_offset(line, column))
    else:
        selection = [lineParts.search(line).groups() for line in selection.splitlines()]
        selection = [[(r'' if part is None else part) for part in line] for line in selection]
        selection = [_commentedLine(line, language, False)[0] for line in selection] #TODO: preferHash~
        document.insert_at_cursor('\n'.join(selection))
    document.end_user_action()

def _uncommentedSpecialCaseLine( line, language, cursorOffset ):
    ## COMMENT/UNCOMMENT
    if ((language == r'cobol') and (line[6] == r'*')):
        line = line[:6] + line[7:]
        return (line, (lineOffset - (lineOffset > 5)))
    elif((language == r'fortran77') and line.startswith((r'C', r'c'))):
        if (line.startswith(r' ')): return ((r'C' + line), (cursorOffset + 1))
        return (line[1:], (cursorOffset - 1))
    return (line, cursorOffset)

def _uncommentedLine( line, language, cursorOffset=0 ):
    ## COMMENT/UNCOMMENT
    limits = None
    if (_emptyLine.match(line)): return (line, cursorOffset)
    if (language in commentSymbol[r'line']):
        limits = (commentSymbol[r'line'][language], r'')
        start = r'(' + re.escape(limits[0]) + r'+)'
        if (language in commentSymbol[r'line#']): start = start[:-1] + r'|#+)'
        commentedLine = re.compile(r'^\s*' + start)
    elif (language in commentSymbol[r'block']):
        limits = commentSymbol[r'block'][language]
        start = r'(' + re.escape(limits[0]) + r')'
        commentedLine = re.compile(r'^\s*' + start + r'.*' + re.escape(limits[1][0]))
    elif(language in commentSymbol[r'special']):
        line, cursorOffset = _uncommentedSpecialCaseLine(line, language, cursorOffset)
    if ((limits is not None) and commentedLine.match(line)):
        finalOffset = cursorOffset
        line = line.rsplit(limits[1], 1) if (len(limits[1]) > 0) else [line, r'']
        line = [re.sub(r'[\t ]+$', r'', line[0]), line[1]]
        if (cursorOffset > len(line[0])): finalOffset -= len(limits[1])
        firstPartLength = len(line[0])
        line = re.split((start + r'\s*'), line[0], 1) + [line[1]]
        if (cursorOffset > len(line[0])): finalOffset -= len(line[1])
        return (r''.join([line[0], line[2], line[3]]), finalOffset)
    return (line, cursorOffset)

def uncommentLines( document ):
    ## COMMENT/UNCOMMENT
    beg, end, noneSelected = getSelectedLines(document, False)
    selection = document.get_text(beg, end, False)
    if (noneSelected and _emptyLine.match(selection)): return
    language = cleanLanguageName(document.get_language().get_name())
    document.begin_user_action()
    document.delete(beg, end)
    if (noneSelected):
        line = document.get_iter_at_mark(document.get_insert())
        column = line.get_line_offset()
        line = line.get_line()
        selection, column = _uncommentedLine(selection, language, column)
        document.insert_at_cursor(selection)
        document.place_cursor(document.get_iter_at_line_offset(line, column))
    else:
        selection = selection.splitlines()
        selection = [_uncommentedLine(line, language)[0] for line in selection]
        document.insert_at_cursor('\n'.join(selection))
    document.end_user_action()



def htmlEncode( document ):
    ## ENCODING STUFF
    beg, end, noneSelected = getSelection(document, False)
    selection = document.get_text(beg, end, False)
    #TODO




def percentEncode( document, doNotEncode=r'' ):
    ## ENCODING STUFF
    beg, end, noneSelected = getSelection(document, False)
    selection = document.get_text(beg, end, False)
    if (noneSelected):
        default = r'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~'
        if (selection in default): return
    doNotEncode = doNotEncode.replace(r'%', r'')
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor(urlquote(selection, doNotEncode, r'utf-8', r'ignore'))
    document.end_user_action()



def percentDecode( document ):
    ## ENCODING STUFF
    beg, end, noneSelected = getSelection(document, False)
    if (noneSelected): end.forward_chars(2)
    selection = document.get_text(beg, end, False)
    if (noneSelected and (not re.match(r'^%[0-9A-Fa-f][0-9A-Fa-f]$', selection))): return
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor(urlunquote(selection, r'utf-8', r'replace'))
    document.end_user_action()



def redecode( document, actualEncoding=r'Autodetect', forceASCIIMode=False ):
    ## ENCODING STUFF
    actualEncoding = actualEncoding.strip().replace(r' ', r'_').lower()
    actualEncoding = re.sub(r'^(code[-_]?page|windows)[-_]?', r'cp', actualEncoding)
    actualEncoding = re.sub(r'^mac[-_]?os[-_]?', r'mac', actualEncoding)
    auto = (actualEncoding == r'autodetect')
    try:
        inUseEncoding = codecLookup(document.get_file().get_encoding().get_charset()).name
        actualEncoding = None if auto else codecLookup(actualEncoding).name
        if (inUseEncoding == actualEncoding): return
        text = document.get_text(document.get_start_iter(), document.get_end_iter(), False)
        text = text.encode(inUseEncoding, r'ignore')
        if (auto):
            actualEncoding = codecLookup(detectEncoding(text)[r'encoding']).name
            if (inUseEncoding == actualEncoding): return #TODO: do this even if not 'auto'
    except:
        return
    text = text.decode(actualEncoding, r'replace')
    if (forceASCIIMode):
        text = unicodeNormalize(r'NFKD', text)
        text = r''.join([c for c in text if not unicodeCombining(c)])
    document.begin_user_action()
    document.delete(document.get_start_iter(), document.get_end_iter())
    try:
        document.insert(document.get_end_iter(), text)
        document.end_user_action()
    except:
        document.end_user_action()
        document.undo()



if (translationIsAvailable):

    translatableLanguages = translatorLANGUAGES

    def translate( document, to ):
        ## TRANSLATE
        beg, end, noneSelected = getSelection(document)
        if (noneSelected and (document.get_language() is not None)): return
        selection = document.get_text(beg, end, False)
        selection = textWrap(selection, 14000,
                expand_tabs=False, replace_whitespace=False, drop_whitespace=False)
        translator = Translator()
        result = r''
        try:
            for chunk in selection:
                result += translator.translate(chunk, src=r'auto', dest=to).text
        except:
            return
        document.begin_user_action()
        document.delete(beg, end)
        document.insert_at_cursor(result)
        document.end_user_action()
else:

    def translate( document, to ):
        ## TRANSLATE
        pass
