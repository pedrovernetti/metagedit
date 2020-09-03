#coding=utf-8

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

import codecs, random, re
import chardet




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
    trailingSpaces = r'[\f\t \u2000-\u200A\u205F\u3000]+$'
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
                beg.set_line_offset(len(re.sub(trailingSpaces, r'', line)))
                end.set_line(lineNumber)
                end.set_line_offset(len(line))
                document.delete(beg, end)
            lineNumber += 1
        removeTrailingNewlines(document)
    else: # selection mode
        selection = re.sub(trailingSpaces, r'', selection, flags=re.MULTILINE)
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



def removeEmptyLines( document ): #TODO: selection mode inserts trailing newlines for some reason
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    document.begin_user_action()
    if (noneSelected): # whole-document mode (doesn't move the cursor)
        for lineNumber in reversed(range(0, (document.get_line_count() - 1))):
            beg.set_line(lineNumber)
            end.set_line(lineNumber)
            if (not end.ends_line()): end.forward_to_line_end()
            if (re.match(r'^\s*$', document.get_text(beg, end, False))):
                end.forward_char()
                document.delete(beg, end)
        removeTrailingNewlines(document)
    else: # selection mode
        selection = document.get_text(beg, end, False)
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
    selection = selection.replace("\n", (r' ' if separatedWithSpaces else r''))
    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor(selection)
    document.end_user_action()



def shuffleLines( document, caseSensitive=False, dedup=False, offset=0 ): #TODO: this whole thing is terrific
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False).splitlines()

    if (dedup and (not sort)):
        seen = set()
        see = seen.add
        selection = [line for line in selection if not (line in seen or see(line))]
    elif (dedup):
        selection = list(set(selection))
    if ((not caseSensitive) and (offset > 0)):
        sortKey = lambda x:(x[offset:]).strip().casefold()
    elif (not caseSensitive):
        sortKey = lambda x:x.strip().casefold()
    elif (offset > 0):
        sortKey = lambda x:x[offset:]
    else: sortKey = lambda x:x.strip()
    random.shuffle(selection)

    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor("\n".join(selection))
    document.end_user_action()



def sortLines( document, sort=True, reverse=False, caseSensitive=False, dedup=False, offset=0 ): #TODO: this whole thing is terrific
    ## LINE OPERATIONS
    beg, end, noneSelected = getSelectedLines(document)
    selection = document.get_text(beg, end, False).splitlines()

    if (dedup and (not sort)):
        seen = set()
        see = seen.add
        selection = [line for line in selection if not (line in seen or see(line))]
    elif (dedup):
        selection = list(set(selection))
    if ((not caseSensitive) and (offset > 0)):
        sortKey = lambda x:(x[offset:]).strip().casefold()
    elif (not caseSensitive):
        sortKey = lambda x:x.strip().casefold()
    elif (offset > 0):
        sortKey = lambda x:x[offset:]
    else: sortKey = lambda x:x.strip()
    if (sort): selection = sorted(selection, key=sortKey)
    if (reverse): selection = reversed(selection)

    document.begin_user_action()
    document.delete(beg, end)
    document.insert_at_cursor("\n".join(selection))
    document.end_user_action()



def redecode( document, actualEncoding=r'Autodetect' ):
    ## ENCODING STUFF
    actualEncoding = actualEncoding.strip().replace(r' ', r'_').lower()
    actualEncoding = re.sub (r'^(code[-_]?page|windows)[-_]?', r'cp', actualEncoding)
    actualEncoding = re.sub (r'^mac[-_]?os[-_]?', r'mac', actualEncoding)
    auto = (actualEncoding == r'autodetect')
    try:
        inUseEncoding = codecs.lookup(document.get_file().get_encoding().get_charset()).name
        actualEncoding = None if auto else codecs.lookup(actualEncoding).name
        if (inUseEncoding == actualEncoding): return
        text = document.get_text(document.get_start_iter(), document.get_end_iter(), False)
        text = text.encode(inUseEncoding, r'ignore')
        if (auto):
            actualEncoding = codecs.lookup(chardet.detect(text)[r'encoding']).name
            if (inUseEncoding == actualEncoding): return
    except:
        return
    document.begin_user_action()
    document.delete(document.get_start_iter(), document.get_end_iter())
    try:
        document.insert(document.get_end_iter(), text.decode(actualEncoding, r'replace'))
        document.end_user_action()
    except:
        document.end_user_action()
        document.undo()
