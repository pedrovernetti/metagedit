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

import re
import iso639
from gi.repository import GObject, Gtk, Gedit

from .textManipulation import *
from .encodingsAndLanguages import *



def showDialog( dialog ):
    if (dialog.window is None): return
    if (not dialog.get_visible()): dialog.show_all()
    else: dialog.present()



## ENCODING STUFF

class EncodingDialog(Gtk.Window):

    def __init__( self ):
        Gtk.Window.__init__(self, title=r'Set Character Encoding',
                                  resizable=False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.window = None
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
        content.pack_start(languageFilterEntry, True, False, 5)
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
        content.pack_start(actualCurrentEncoding, True, False, 5)
        self.setEncodingButton = Gtk.Button(label=r'Looks Good')
        self.setEncodingButton.connect(r'clicked', self._setEncoding)
        content.pack_start(self.setEncodingButton, True, True, 5)
        ASCIIButton = Gtk.Button(label=r'Agressively Convert to ASCII')
        ASCIIButton.connect(r'clicked', self._toASCIIForced)
        content.pack_start(ASCIIButton, True, True, 5)
        ASCIIButton.set_sensitive(False) # This functionality needs to be improved
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        self.setEncodingButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        if (self.window is None): return
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

    def setMainWindow( self, window ):
        self.window = window
        self.set_transient_for(window)



class PercentEncodeDialog(Gtk.Window):

    def __init__( self ):
        Gtk.Window.__init__(self, title=r'Percent-Encoding',
                                  resizable=False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.window = None
        self.ignoreListEntry = Gtk.Entry(placeholder_text=r'Characters to leave unencoded')
        self.ignoreListEntry.set_tooltip_text(r'Characters to leave unencoded')
        self.ignoreListEntry.set_width_chars(40)
        self.ignoreListEntry.set_alignment(0.5)
        content.pack_start(self.ignoreListEntry, True, True, 5)
        encodeButton = Gtk.Button(label=r'Encode')
        encodeButton.connect(r'clicked', self._encode)
        content.pack_start(encodeButton, True, True, 5)
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        encodeButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        if (self.window is None): return #TODO hide

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _encode( self, widget ):
        percentEncode(self.window.get_active_document(), self.ignoreListEntry.get_text())
        self.hide()

    def setMainWindow( self, window ):
        self.window = window
        self.set_transient_for(window)



encodingDialog = EncodingDialog()
percentEncodeDialog = PercentEncodeDialog()



## LINE OPERATIONS

class SortDialog(Gtk.Window):

    def __init__( self ):
        Gtk.Window.__init__(self, title=r'Sort Lines',
                                  resizable=False)
        self.reverse = False
        self.dedup = False
        self.case = False
        self.window = None
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        reverseSort = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        reverseSortToggle = Gtk.CheckButton(active=False, label=r'Reverse Order')
        reverseSortToggle.connect(r'toggled', self._setReverse)
        content.pack_start(reverseSortToggle, True, False, 2)
        dedupSortToggle = Gtk.CheckButton(active=False, label=r'Remove Duplicates')
        dedupSortToggle.connect(r'toggled', self._setDedup)
        content.pack_start(dedupSortToggle, True, False, 2)
        caseSortToggle = Gtk.CheckButton(active=False, label=r'Case-sensitive')
        caseSortToggle.connect(r'toggled', self._setCase)
        content.pack_start(caseSortToggle, True, False, 2)
        sortOffset = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sortOffsetLabel = Gtk.Label(label='Ignore lines\x27 first N characters:')
        sortOffset.pack_start(sortOffsetLabel, False, True, 10)
        self._sortOffsetEntry = Gtk.Entry(text=r'0')
        self._sortOffsetEntry.set_max_width_chars(3)
        self._sortOffsetEntry.set_width_chars(3)
        sortOffset.pack_start(self._sortOffsetEntry, True, True, 0)
        content.pack_start(sortOffset, True, False, 5)
        sortButton = Gtk.Button(label=r'Sort')
        sortButton.connect(r'clicked', self._sort)
        content.pack_start(sortButton, True, True, 5)
        dedupButton = Gtk.Button(label=r'Remove Duplicates (no sorting)')
        dedupButton.connect(r'clicked', self._dedup)
        content.pack_start(dedupButton, True, True, 5)
        shuffleButton = Gtk.Button(label=r'Shuffle')
        shuffleButton.connect(r'clicked', self._shuffle)
        content.pack_start(shuffleButton, True, True, 5)
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        sortButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        if (self.window is None): return

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _setReverse( self, button ):
        self.reverse = button.get_active()

    def _setDedup( self, button ):
        self.dedup = button.get_active()

    def _setCase( self, button ):
        self.case = button.get_active()

    def _getOffset( self ):
        offset = self._sortOffsetEntry.get_text().strip()
        return (int(offset) if offset else 0)

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

    def setMainWindow( self, window ):
        self.window = window
        self.set_transient_for(window)



sortDialog = SortDialog()



## SESSIONS

class SaveSessionDialog(Gtk.Window):

    def __init__( self ):
        Gtk.Window.__init__(self, title=r'Save Session',
                                  resizable=False)
        self.window = None
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.sessionNameEntry = Gtk.Entry(placeholder_text=r'Session Name')
        self.sessionNameEntry.set_width_chars(40)
        self.sessionNameEntry.set_max_length(40)
        self.sessionNameEntry.set_alignment(0.5)
        content.pack_start(self.sessionNameEntry, True, True, 5)
        saveButton = Gtk.Button(label=r'Save')
        saveButton.connect(r'clicked', self._saveSession)
        content.pack_start(saveButton, True, True, 5)
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        saveButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        if (self.window is None): return
        self.sessionNameEntry.set_text(self.window.metageditActivatable.suggestedSessionName())

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _saveSession( self, widget ):
        self.window.metageditActivatable.saveSession(self.sessionNameEntry.get_text())
        self.hide()

    def setMainWindow( self, window ):
        self.window = window
        self.set_transient_for(window)



class ManageSessionsDialog(Gtk.Window): #TODO

    def __init__( self ):
        Gtk.Window.__init__(self, title=r'Save Session',
                                  resizable=False)
        self.window = None
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.sessionNameEntry = Gtk.Entry(placeholder_text=r'Session Name')
        self.sessionNameEntry.set_width_chars(40)
        self.sessionNameEntry.set_max_length(40)
        self.sessionNameEntry.set_alignment(0.5)
        content.pack_start(self.sessionNameEntry, True, True, 5)
        saveButton = Gtk.Button(label=r'Save')
        saveButton.connect(r'clicked', self._saveSession)
        content.pack_start(saveButton, True, True, 5)
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        saveButton.grab_focus()

    def _onShow( self, widget=None, event=None ):
        if (self.window is None): return
        self.sessionNameEntry.set_text(self.window.metageditActivatable.suggestedSessionName())

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _saveSession( self, widget ):
        self.window.metageditActivatable.saveSession(self.sessionNameEntry.get_text())
        self.hide()

    def setMainWindow( self, window ):
        self.window = window
        self.set_transient_for(window)



saveSessionDialog = SaveSessionDialog()
manageSessionsDialog = ManageSessionsDialog()
