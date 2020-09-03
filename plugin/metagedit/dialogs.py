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



class EncodingDialog(Gtk.Window):

    def __init__( self, geditView ):
        ## ENCODING STUFF
        Gtk.Window.__init__(self, title=r'Set Character Encoding',
                                  transient_for=geditView.get_toplevel(),
                                  resizable=False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.view = geditView
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
        encodingStore = Gtk.ListStore(str)
        encodingStore.append([r'Autodetect']) #TODO: set as default
        for encoding in supportedEncodings():
            encodingStore.append([encoding])
        actualCurrentEncodingEntry = Gtk.ComboBox.new_with_model(encodingStore)
        actualCurrentEncodingEntry.connect(r'changed', self._onEncodingChanged)
        actualCurrentEncodingText = Gtk.CellRendererText()
        actualCurrentEncodingEntry.pack_start(actualCurrentEncodingText, True)
        actualCurrentEncodingEntry.add_attribute(actualCurrentEncodingText, r'text', 0)
        actualCurrentEncoding.pack_start(actualCurrentEncodingEntry, True, True, 0)
        content.pack_start(actualCurrentEncoding, True, False, 5)
        UTF8Button = Gtk.Button(label=r'Convert to UTF-8')
        UTF8Button.connect(r'clicked', self._convertEncoding)
        content.pack_start(UTF8Button, True, True, 5)
        ASCIIButton = Gtk.Button(label=r'Convert to ASCII (forced)')
        ASCIIButton.connect(r'clicked', self._toASCIIForced)
        content.pack_start(ASCIIButton, True, True, 5)
        self.add(content)
        self.connect(r'delete-event', self._onDestroy)
        UTF8Button.grab_focus()

    def _onLanguageChanged( self, combo ): #TODO: limit encoding combobox options
        i = combo.get_active_iter()
        if (i is not None):
            iso6392B, language = combo.get_model()[i][:2]
            print("Selected: ISO6392=%s, name=%s" % (iso6392b, language))
        else:
            language = re.sub(r'\s+', r' ', combo.get_child().get_text().strip().capitalize())
            if (len(language) < 2): return
            try: iso6392B = iso639.languages.name.get(language).part2b
            except: iso6392B = r'und'
            if (iso6392B in {r'', r'mul', r'und', r'zxx'}): return
            print("Selected: ISO6392=%s, name=%s" % (iso6392B, language))

    def _onEncodingChanged( self, combo ): #TODO: set encoding and preview it (apply -> undo+apply -> undo+apply -> ...)
        pass

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _convertEncoding( self, widget ):
        encoding = self._actualCurrentEncodingEntry.get_text().strip() #TODO: get encoding combobox value
        redecode(self.view.get_buffer(), encoding)
        self.hide()

    def _toASCIIForced( self, widget ):
        pass #TODO: remove diacritics, convert unicode spaces to 0x20, strip other chars, etc., then re-encode



class SortDialog(Gtk.Window):

    def __init__( self, geditView ):
        Gtk.Window.__init__(self, title=r'Sort Lines',
                                  transient_for=geditView.get_toplevel(),
                                  resizable=False)
        self.reverse = False
        self.dedup = False
        self.case = False
        self.view = geditView
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
        self.connect(r'delete-event', self._onDestroy)
        sortButton.grab_focus()

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _setReverse( self, button ):
        self.reverse = button.get_active()

    def _setDedup( self, button ):
        self.dedup = button.get_active()

    def _setCase( self, button ):
        self.case = button.get_active()

    def _getOffset( self, button ):
        offset = self._sortOffsetEntry.get_text().strip()
        return (int(offset) if offset else 0)

    def _dedup( self, widget ):
        sortLines(self.view.get_buffer(), False, self.reverse, self.case, self.dedup, self._getOffset())
        self.hide()

    def _shuffle( self, widget ):
        shuffleLines(self.view.get_buffer(), self.case, self.dedup, offset)
        self.hide()

    def _sort( self, widget ):
        sortLines(self.view.get_buffer(), True, self.reverse, self.case, self.dedup, self._getOffset())
        self.hide()
