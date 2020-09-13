
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
from time import localtime, strftime
from os import listdir, stat, rename
import iso639
from gi.repository import GObject, Gtk, Gedit

from .textManipulation import *
from .encodingsAndLanguages import *



def showDialog( dialog ):
    if (dialog.window is None): return
    if (not dialog.get_visible()): dialog.show_all()
    else: dialog.present()



class MetageditDialog(Gtk.Window):

    def __init__( self, geditWindow, title ):
        Gtk.Window.__init__(self, title=title, transient_for=geditWindow, resizable=False)
        self.window = geditWindow
        self.connect(r'delete-event', self._onDestroy)
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self._content.set_border_width(10)
        self.add(self._content)

    def pack( self, widget, expand, fill, padding ):
        self._content.pack_start(widget, expand, fill, padding)

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True



## ENCODING STUFF

class EncodingDialog(MetageditDialog):

    def __init__( self, geditWindow ):
        MetageditDialog.__init__(self, geditWindow, r'Set Character Encoding')
        self.previewing = False
        languageStore = Gtk.ListStore(str, str)
        seenLanguages = set()
        for language in iso639.languages.name.values():
            if ((len(language.part2b) == 3) and (language.part2b not in seenLanguages)):
                languageStore.append([language.part2b, language.name])
                seenLanguages.add(language.part2b)
        languageFilterEntry = Gtk.ComboBox.new_with_model_and_entry(languageStore)
        languageFilterEntry.connect(r'changed', self._onLanguageChanged)
        languageFilterEntry.set_entry_text_column(1)
        languageFilterEntry.set_tooltip_text(r'Filter possible encodings by language')
        languageFilterEntry.get_child().set_placeholder_text(r'Filter possible encodings by language')
        self.pack(languageFilterEntry, True, False, 0)
        actualCurrentEncoding = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        actualCurrentEncodingLabel = Gtk.Label(label=r'Treat Current Encoding as:')
        actualCurrentEncoding.pack_start(actualCurrentEncodingLabel, False, True, 10)
        self.actualCurrentEncodingEntry = Gtk.ComboBox()
        self._setEncodingCombo()
        self.actualCurrentEncodingEntry.connect(r'changed', self._onEncodingChanged)
        actualCurrentEncodingText = Gtk.CellRendererText()
        self.actualCurrentEncodingEntry.pack_start(actualCurrentEncodingText, True)
        self.actualCurrentEncodingEntry.add_attribute(actualCurrentEncodingText, r'text', 0)
        self.actualCurrentEncodingEntry.set_active(0)
        actualCurrentEncoding.pack_start(self.actualCurrentEncodingEntry, True, True, 0)
        self.pack(actualCurrentEncoding, True, False, 0)
        self.setEncodingButton = Gtk.Button(label=r'Looks Good')
        self.setEncodingButton.connect(r'clicked', self._setEncoding)
        self.pack(self.setEncodingButton, True, True, 0)
        ASCIIButton = Gtk.Button(label=r'Agressively Convert to ASCII')
        ASCIIButton.connect(r'clicked', self._toASCIIForced)
        self.pack(ASCIIButton, True, True, 0)
        ASCIIButton.set_sensitive(False) #TODO: This functionality needs to be improved
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        self.setEncodingButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        self.setEncodingButton.set_sensitive(False)
        self.previewing = False
        self.actualCurrentEncodingEntry.set_active(0)

    def _setEncodingCombo( self, language=r'mul' ):
        encodingStore = Gtk.ListStore(str)
        encodingStore.append([r'Autodetect'])
        seenEncodings = set()
        for encoding in supportedEncodings(language):
            encodingNormalized = encoding.casefold().strip()
            if (encodingNormalized not in seenEncodings):
                encodingStore.append([encoding])
                seenEncodings.add(encodingNormalized)
        if (self.previewing): self.window.get_active_document().undo()
        self.actualCurrentEncodingEntry.set_model(encodingStore)
        self.actualCurrentEncodingEntry.set_active(0)

    def _onLanguageChanged( self, combo ):
        i = combo.get_active_iter()
        if (i is not None):
            iso6392B, language = combo.get_model()[i][:2]
            self._setEncodingCombo(iso6392B)
        else:
            language = re.sub(r'\s+', r' ', combo.get_child().get_text().strip().capitalize())
            if (len(language) < 2): return
            try: iso6392B = iso639.languages.name.get(language).part2b
            except: iso6392B = r'und'
            if (iso6392B in {r'', r'mul', r'und', r'zxx'}): return
            self._setEncodingCombo(iso6392B)

    def _onEncodingChanged( self, combo ):
        i = combo.get_active_iter()
        if (i is not None):
            encoding = combo.get_model()[i][0]
            if (self.previewing): self.window.get_active_document().undo()
            self.previewing = True
            redecode(self.window.get_active_document(), encoding)
            self.setEncodingButton.set_sensitive(True)

    def _onDestroy( self, widget=None, event=None ):
        if (self.previewing): self.window.get_active_document().undo()
        self.hide()
        return True

    def _setEncoding( self, widget ):
        self.hide()

    def _toASCIIForced( self, widget ):
        if (self.previewing): self.window.get_active_document().undo()
        i = self.actualCurrentEncodingEntry.get_active_iter()
        if (i is not None):
            encoding = self.actualCurrentEncodingEntry.get_model()[i][0]
            redecode(self.window.get_active_document(), encoding, True)
        self.hide()



class PercentEncodeDialog(MetageditDialog):

    def __init__( self, geditWindow ):
        MetageditDialog.__init__(self, geditWindow, r'Percent-Encoding')
        self.ignoreListEntry = Gtk.Entry(placeholder_text=r'Characters to leave unencoded')
        self.ignoreListEntry.set_tooltip_text(r'Characters to leave unencoded')
        self.ignoreListEntry.set_width_chars(40)
        self.ignoreListEntry.set_alignment(0.5)
        self.pack(self.ignoreListEntry, True, True, 0)
        encodeButton = Gtk.Button(label=r'Encode')
        encodeButton.connect(r'clicked', self._encode)
        self.pack(encodeButton, True, True, 0)
        encodeButton.grab_focus()

    def _encode( self, widget ):
        percentEncode(self.window.get_active_document(), self.ignoreListEntry.get_text())
        self.hide()



## LINE OPERATIONS

class SortDialog(MetageditDialog):

    def __init__( self, geditWindow ):
        MetageditDialog.__init__(self, geditWindow, r'Sort Lines')
        self.reverse = False
        self.dedup = False
        self.case = False
        toggles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        reverseSortToggle = Gtk.CheckButton(active=False, label=r'Reverse Order')
        reverseSortToggle.connect(r'toggled', self._setReverse)
        toggles.pack_start(reverseSortToggle, True, False, 0)
        dedupSortToggle = Gtk.CheckButton(active=False, label=r'Remove Duplicates')
        dedupSortToggle.connect(r'toggled', self._setDedup)
        toggles.pack_start(dedupSortToggle, True, False, 0)
        caseSortToggle = Gtk.CheckButton(active=False, label=r'Case-sensitive')
        caseSortToggle.connect(r'toggled', self._setCase)
        toggles.pack_start(caseSortToggle, True, False, 0)
        self.pack(toggles, True, False, 0)
        sortOffset = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sortOffsetLabel = Gtk.Label(label='Ignore lines\x27 first N characters:')
        sortOffset.pack_start(sortOffsetLabel, False, True, 10)
        self._sortOffsetEntry = Gtk.SpinButton(value=0, digits=0, numeric=True)
        self._sortOffsetEntry.set_increments(1, 5)
        self._sortOffsetEntry.set_range(0, 999)
        sortOffset.pack_start(self._sortOffsetEntry, True, True, 0)
        self.pack(sortOffset, True, False, 0)
        sortButton = Gtk.Button(label=r'Sort')
        sortButton.connect(r'clicked', self._sort)
        self.pack(sortButton, True, True, 0)
        dedupButton = Gtk.Button(label=r'Remove Duplicates (no sorting)')
        dedupButton.connect(r'clicked', self._dedup)
        self.pack(dedupButton, True, True, 0)
        shuffleButton = Gtk.Button(label=r'Shuffle')
        shuffleButton.connect(r'clicked', self._shuffle)
        self.pack(shuffleButton, True, True, 0)
        sortButton.grab_focus()

    def _setReverse( self, button ):
        self.reverse = button.get_active()

    def _setDedup( self, button ):
        self.dedup = button.get_active()

    def _setCase( self, button ):
        self.case = button.get_active()

    def _getOffset( self ):
        return self._sortOffsetEntry.get_value_as_int()

    def _dedup( self, widget ):
        self.window.get_active_document().begin_user_action()
        dedupLines(self.window.get_active_document(), self.case, self._getOffset())
        if (self.reverse): reverseLines(self.window.get_active_document())
        self.window.get_active_document().end_user_action()
        self.hide()

    def _shuffle( self, widget ):
        shuffleLines(self.window.get_active_document(), self.dedup, self.case, self._getOffset())
        self.hide()

    def _sort( self, widget ):
        sortLines(self.window.get_active_document(), self.reverse, self.dedup, self.case, self._getOffset())
        self.hide()



## SESSIONS

class SessionDialog(MetageditDialog):

    def __init__( self, geditWindow, title, sessionsFolder ):
        MetageditDialog.__init__(self, geditWindow, title)
        self.sessionsFolder = sessionsFolder
        self.forbiddenCharacters = re.compile(r'[^\w .-]')
        self.sessionNameEntry = Gtk.Entry()
        self.sessionNameEntry.set_max_length(40)
        self.sessionNameEntry.connect(r'insert_text', lambda e, t, l, p: self._sessionNameChanged())

    def _filterSessionName( self ):
        name = self.sessionNameEntry.get_text()
        position = self.sessionNameEntry.get_position()
        name = (re.sub(self.forbiddenCharacters, r'', name[0:position]),
                re.sub(self.forbiddenCharacters, r'', name[position:]))
        self.sessionNameEntry.set_text(r''.join(name))
        self.sessionNameEntry.set_position(len(name[0]))

    def _sessionNameChanged( self ):
        GObject.idle_add(self._filterSessionName)



class SaveSessionDialog(SessionDialog):

    def __init__( self, geditWindow, sessionsFolder ):
        SessionDialog.__init__(self, geditWindow, r'Save Session', sessionsFolder)
        self.sessionNameEntry.set_placeholder_text(r'Session Name')
        self.sessionNameEntry.set_width_chars(40)
        self.sessionNameEntry.set_alignment(0.5)
        self.pack(self.sessionNameEntry, True, True, 0)
        self.saveButton = Gtk.Button(label=r'Save')
        self.saveButton.connect(r'clicked', self._saveSession)
        self.pack(self.saveButton, True, True, 0)
        self.connect(r'show', self._onShow)
        self.saveButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        self.sessionNameEntry.set_text(
                self.window.get_active_document().get_short_name_for_display())

    def _saveSession( self, widget ):
        session = self.sessionNameEntry.get_text()
        if (session in listdir(self.sessionsFolder)): return
        self.window.metageditActivatable.saveSession(session)
        self.hide()



class ManageSessionsDialog(SessionDialog):

    def __init__( self, geditWindow, sessionsFolder ):
        SessionDialog.__init__(self, geditWindow, r'Manage Sessions', sessionsFolder)
        self.sessionsList = Gtk.TreeView()
        columnsExpand = (True, False, False)
        for i, columnTitle in enumerate([r'Session', r'Tabs', r'Saved']):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(columnTitle, renderer, text=i)
            column.set_expand(columnsExpand[i])
            self.sessionsList.append_column(column)
        sessionsColumn = Gtk.TreeViewColumn(r'Session', renderer, text=0)
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(600)
        scrolled.set_propagate_natural_width(True)
        scrolled.add(self.sessionsList)
        self.pack(scrolled, True, True, 0)
        self.buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttonsGroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        openButton = Gtk.Button(label=r'Load')
        openButton.connect(r'clicked', self._loadSession)
        self.buttons.pack_start(openButton, True, True, 0)
        buttonsGroup.add_widget(openButton)
        self.renameButton = Gtk.ToggleButton(label=r'Rename')
        self.renameButton.connect(r'toggled', lambda b: self._toggleRename())
        self.buttons.pack_start(self.renameButton, True, False, 0)
        buttonsGroup.add_widget(self.renameButton)
        editButton = Gtk.Button(label=r'Edit')
        editButton.connect(r'clicked', self._editSession)
        editButton.set_tooltip_text(
                r'Sessions are stored as TSVs, each row being: \
                <active tab>, <line>, <column>, <encoding>, <file URI>')
        self.buttons.pack_start(editButton, True, True, 0)
        buttonsGroup.add_widget(editButton)
        deleteButton = Gtk.Button(label=r'Delete')
        deleteButton.connect(r'clicked', self._removeSession)
        deleteButton.set_tooltip_text(r'⚠️   No confirmation will be asked!')
        self.buttons.pack_start(deleteButton, True, True, 0)
        buttonsGroup.add_widget(deleteButton)
        self.pack(self.buttons, False, True, 0)
        self.renameSession = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.sessionNameEntry.set_placeholder_text(r'New Session Name')
        self.renameSession.pack_start(self.sessionNameEntry, True, True, 0)
        applyNameButton = Gtk.Button(label=r'Apply')
        applyNameButton.connect(r'clicked', self._renameSession)
        self.renameSession.pack_start(applyNameButton, False, True, 0)
        self.pack(self.renameSession, True, True, 0)
        self.connect(r'show', self._onShow)
        self.sessionsList.grab_focus()
        # overwrite with current, save current

    def _onShow( self, widget=None, event=None ):
        self._updateSessionsList()
        self.renameButton.set_active(False)
        self.renameSession.hide()

    def _updateSessionsList( self ):
        sessionsStore = Gtk.ListStore(str, int, str)
        for session in listdir(self.sessionsFolder):
            try: tabs = len(open(self.sessionsFolder + session, r'r').read().splitlines())
            except: continue
            mtime = localtime(stat(self.sessionsFolder + session).st_mtime)
            mtime = strftime(r'%Y-%m-%d %H:%M:%S ', mtime)
            sessionsStore.append([session, tabs, mtime])
        self.sessionsList.set_model(sessionsStore)

    def _loadSession( self, widget ):
        model, paths = self.sessionsList.get_selection().get_selected_rows()
        for path in paths:
            session = model.get_value(model.get_iter(path), 0)
            self.window.metageditActivatable.loadSession(session)

    def _toggleRename( self ):
        self.renameSession.set_visible(self.renameButton.get_active())

    def _renameSession( self, widget ):
        model, paths = self.sessionsList.get_selection().get_selected_rows()
        newName = self.sessionNameEntry.get_text()
        if (newName in listdir(self.sessionsFolder)): return
        session = model.get_value(model.get_iter(paths[0]), 0)
        try: rename(self.sessionsFolder + session, self.sessionsFolder + newName)
        except: return
        self.window.metageditActivatable.removeSession(session)
        self.window.metageditActivatable.registerSession(newName)
        self._updateSessionsList()
        self.window.get_application().metageditActivatable.updateMenuSessions()
        self.renameButton.set_active(False)
        self._toggleRename()

    def _editSession( self, widget ):
        model, paths = self.sessionsList.get_selection().get_selected_rows()
        for path in paths:
            session = model.get_value(model.get_iter(path), 0)
            self.window.metageditActivatable.editSession(session)

    def _removeSession( self, widget ):
        model, paths = self.sessionsList.get_selection().get_selected_rows()
        for path in paths:
            session = model.get_value(model.get_iter(path), 0)
            self.window.metageditActivatable.removeSession(session)
        self._updateSessionsList()



## DOCUMENT STATS

class DocumentStatsDialog(MetageditDialog):

    def __init__( self, geditWindow ):
        MetageditDialog.__init__(self, geditWindow, r'Document Statistics')
        self.windowHandler = None
        self.document = None
        self.documentHandler = None
        self.view = None
        self.viewHandler = None
        self.set_default_size(300, -1)
        content = Gtk.Grid()
        content.set_column_spacing(20)
        content.set_row_spacing(6)
        documentHeaderLabel = Gtk.Label(label=r'Document', xalign=1.0)
        documentHeaderLabel.set_markup(r'<b>Document</b>')
        content.attach(documentHeaderLabel, 3, 0, 1, 1)
        selectionHeaderLabel = Gtk.Label(label=r'Selection', xalign=1.0)
        selectionHeaderLabel.set_markup(r'<b>Selection</b>')
        content.attach(selectionHeaderLabel, 4, 0, 1, 1)
        linesLabel = Gtk.Label(label=r'Lines', xalign=0.0)
        content.attach(linesLabel, 0, 1, 3, 1)
        self.lines = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.lines, 3, 1, 1, 1)
        self.selectedLines = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.selectedLines, 4, 1, 1, 1)
        wordsLabel = Gtk.Label(label=r'Words', xalign=0.0)
        content.attach(wordsLabel, 0, 2, 3, 1)
        self.words = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.words, 3, 2, 1, 1)
        self.selectedWords = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.selectedWords, 4, 2, 1, 1)
        charactersLabel = Gtk.Label(label=r'Characters (incl. spaces)', xalign=0.0)
        content.attach(charactersLabel, 0, 3, 3, 1)
        self.characters = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.characters, 3, 3, 1, 1)
        self.selectedCharacters = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.selectedCharacters, 4, 3, 1, 1)
        charactersNotSpacesLabel = Gtk.Label(label=r'Characters (no spaces)', xalign=0.0)
        content.attach(charactersNotSpacesLabel, 0, 4, 3, 1)
        self.charactersNotSpaces = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.charactersNotSpaces, 3, 4, 1, 1)
        self.selectedCharactersNotSpaces = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.selectedCharactersNotSpaces, 4, 4, 1, 1)
        bytesLabel = Gtk.Label(label=r'UTF-8 Code Units (bytes)', xalign=0.0)
        content.attach(bytesLabel, 0, 5, 3, 1)
        self.bytes = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.bytes, 3, 5, 1, 1)
        self.selectedBytes = Gtk.Label(label=r'-', xalign=1.0, selectable=True)
        content.attach(self.selectedBytes, 4, 5, 1, 1)
        self.pack(content, True, True, 5)
        self.connect(r'focus-in-event', lambda e, d: self._updateSelection())
        self.connect(r'focus-out-event', lambda e, d: self._updateSelection())
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        content.grab_focus()

    def _updateDocument( self ):
        lines = self.document.get_line_count()
        words = 0
        i = self.document.get_start_iter()
        while i.forward_visible_word_end(): words += 1
        characters = self.document.get_char_count()
        i = self.document.get_start_iter()
        charactersNotSpaces = characters
        end = self.document.get_end_iter()
        charactersNotSpaces -= len(re.findall(r'\s', self.document.get_text(i, end, False)))
        bytes = i.get_bytes_in_line()
        while i.forward_visible_line(): bytes += i.get_bytes_in_line()
        self.lines.set_text(str(lines))
        self.words.set_text(str(words))
        self.characters.set_text(str(characters))
        self.charactersNotSpaces.set_text(str(charactersNotSpaces))
        self.bytes.set_text(str(bytes))

    def _updateSelection( self ):
        if (not self.document.get_has_selection()):
            self.selectedBytes.set_text(r'-')
            self.selectedCharacters.set_text(r'-')
            self.selectedCharactersNotSpaces.set_text(r'-')
            self.selectedLines.set_text(r'-')
            self.selectedWords.set_text(r'-')
            return
        beg, end = self.document.get_selection_bounds()
        words = 0
        i = self.document.get_selection_bounds()[0]
        if (not end.inside_word()): words = -1
        while i.in_range(beg, end) and i.forward_visible_word_end(): words += 1
        lines = 0
        i = self.document.get_selection_bounds()[0]
        while i.in_range(beg, end) and i.forward_visible_line(): lines += 1
        text = self.document.get_text(beg, end, False)
        bytes = len(text.encode(r'utf-8', r'ignore'))
        self.selectedBytes.set_text(str(bytes))
        self.selectedCharacters.set_text(str(len(text)))
        self.selectedCharactersNotSpaces.set_text(str(len(text) - len(re.findall(r'\s', text))))
        self.selectedLines.set_text(str(lines))
        self.selectedWords.set_text(str(words))

    def _refresh( self ):
        if (self.document is None):
            self.bytes.set_text(r'-')
            self.characters.set_text(r'-')
            self.charactersNotSpaces.set_text(r'-')
            self.lines.set_text(r'-')
            self.words.set_text(r'-')
            return
        self._updateDocument()
        self._updateSelection()

    def _change( self ):
        if (self.documentHandler is not None): self.document.disconnect(self.documentHandler)
        if (self.viewHandler is not None): self.view.disconnect(self.viewHandler)
        self.document = self.window.get_active_document()
        self.view = self.window.get_active_view()
        if (self.document.get_char_count() < 300000): # no auto-refresh for too large documents
            self.documentHandler = self.document.connect(r'changed', lambda d: GObject.idle_add(self._refresh))
        self.viewHandler = self.view.connect(r'move-cursor', lambda s, c, x, d: GObject.idle_add(self._updateSelection))
        self._updateDocument()
        self._updateSelection()

    def _onShow( self, widget=None, event=None ):
        self.windowHandler = self.window.connect(r'active_tab_changed', lambda w, t: self._change())
        self._change()

    def _onDestroy( self, widget=None, event=None ):
        if (self.windowHandler is not None): self.window.disconnect(self.windowHandler)
        if (self.documentHandler is not None): self.document.disconnect(self.documentHandler)
        if (self.viewHandler is not None): self.view.disconnect(self.viewHandler)
        self.hide()
        return True



## PICK COLOR

class PickColorDialog(MetageditDialog):

    def __init__( self, geditWindow ):
        MetageditDialog.__init__(self, geditWindow, r'Pick Color')
        self.useAlpha = False
        self.uppercaseHex = False
        toggles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        alphaToggle = Gtk.CheckButton(active=False, label=r'Use Alpha Channel')
        alphaToggle.connect(r'toggled', self._setAlpha)
        toggles.pack_start(alphaToggle, True, False, 0)
        uppercaseHexToggle = Gtk.CheckButton(active=False, label=r'Uppercase Hex Code')
        uppercaseHexToggle.connect(r'toggled', self._setUppercaseHex)
        toggles.pack_start(uppercaseHexToggle, True, False, 0)
        self.pack(toggles, True, False, 0)
        self.colorPicker = Gtk.ColorChooserWidget(show_editor=True)
        self.colorPicker.set_use_alpha(False)
        self.pack(self.colorPicker, True, True, 0)
        CMYKScaleRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        CMYKScaleLabel = Gtk.Label(label='CMYK Scale:')
        CMYKScaleRow.pack_start(CMYKScaleLabel, False, True, 0)
        self.CMYKScaleEntry = Gtk.Entry(text=r'100')
        self.CMYKScaleEntry.set_tooltip_text(r'CMYK Scale')
        self.CMYKScaleEntry.set_max_length(4)
        self.CMYKScaleEntry.set_alignment(1.0)
        CMYKScaleRow.pack_start(self.CMYKScaleEntry, True, True, 0)
        self.pack(CMYKScaleRow, True, True, 0)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        buttonsGroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        PickHexButton = Gtk.Button(label=r'Hex Code')
        PickHexButton.connect(r'clicked', self._pickHex)
        buttons.pack_start(PickHexButton, True, True, 0)
        buttonsGroup.add_widget(PickHexButton)
        PickRGBButton = Gtk.Button(label=r'RGB(A) Tuple')
        PickRGBButton.connect(r'clicked', self._pickRGB)
        buttons.pack_start(PickRGBButton, True, True, 0)
        buttonsGroup.add_widget(PickRGBButton)
        PickCMYKButton = Gtk.Button(label=r'CMYK Tuple')
        PickCMYKButton.connect(r'clicked', self._pickCMYK)
        buttons.pack_start(PickCMYKButton, True, True, 0)
        buttonsGroup.add_widget(PickCMYKButton)
        self.pack(buttons, True, True, 0)
        self.colorPicker.grab_focus()

    def _setAlpha( self, button ):
        self.useAlpha = button.get_active()
        self.colorPicker.set_use_alpha(self.useAlpha)

    def _setUppercaseHex( self, button ):
        self.uppercaseHex = button.get_active()

    def _pick( self, colorString ):
        self.window.get_active_document().insert_at_cursor(colorString)
        self.hide()

    def _pickHex( self, widget ):
        RGBA = self.colorPicker.get_rgba()
        colorString = r'#' + hex(round(255 * RGBA.red))[2:]
        colorString += hex(round(255 * RGBA.green))[2:]
        colorString += hex(round(255 * RGBA.blue))[2:]
        if (self.useAlpha): colorString += hex(round(255 * RGBA.alpha))[2:]
        if (self.uppercaseHex): colorString = colorString.upper()
        self._pick(colorString)

    def _pickRGB( self, widget ):
        colorString = self.colorPicker.get_rgba().to_string()
        self._pick(colorString)

    def _pickCMYK( self, widget ):
        scale = self.CMYKScaleEntry.get_text().strip()
        scale = (int(scale) if re.match(r'^[0-9]+$', scale) else 100)
        RGBA = self.colorPicker.get_rgba()
        r, g, b = (RGBA.red, RGBA.green, RGBA.blue)
        if ((r, g, b) == (0, 0, 0)):
            self._pick(r'cmyk(0,0,0,' + str(scale) + r')')
        else:
            c, m, y = ((1 - r), (1 - g), (1 - b))
            k = min(c, m, y)
            c, m, y = ((c - k), (m - k), (y - k))
            c, m, y, k = [round(x * scale) for x in (c, m, y, k)]
            colorString = r'cmyk(' + str(c) + r',' + str(m) + r','
            colorString += (str(y) + r',' + str(k) + r')')
            self._pick(colorString)
