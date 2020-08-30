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
# #  In order to have this script working (if it is currently not), run 'install.sh'. In case
#    it is missing or does not work, follow these steps:
# 1. install pip3 (Python package installer) using your package manager;  .
      # 2. with pip, install lxml, pymediainfo, mutagen, mido, pillow, pyexiv2, .
      #    pypdf2, olefile and torrentool;                                      .
# 3. create a subfolder named "metagedit" at the gedit plugins folder     .
#    (which uses to be "/usr/lib/x86_64-linux-gnu/gedit/plugins");        .
# 4. place this file, together with every other python file that has came .
#    together with it, inside that just created "metagedit" subfolder;    .
# 5. place at the gedit plugins folder (not the subfolder) the file named .
#    'metagedit.plugin', that must also have came together with this file .
#    you're reading (but not in the same folder);                         .
# 6. open or restart gedit, then go to is Preferences > Plugins and check .
#    the entry for this plugin ("Metagedit").                             .
#
# =============================================================================================

from gi.repository import GObject, Gtk, Gedit



class EncodingDialog(Gtk.Window):

    def __init__( self, geditView ):
        Gtk.Window.__init__(self, title=r'Character Encoding',
                                  transient_for=geditView.get_toplevel(),
                                  modal=True,
                                  resizable=False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.view = geditView

        languageFilterEntry = Gtk.Entry(placeholder_text=r'Filter possible encodings by language')
        languageFilterEntry.set_max_width_chars(30)
        languageFilterEntry.set_width_chars(30)
        content.pack_start(languageFilterEntry, True, False, 5)

        actualCurrentEncoding = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        actualCurrentEncodingLabel = Gtk.Label(label=r'Treat Current Encoding as:')
        actualCurrentEncoding.pack_start(actualCurrentEncodingLabel, False, True, 10)
        self._actualCurrentEncodingEntry = Gtk.Entry(text=r'Autodetect')
        self._actualCurrentEncodingEntry.set_max_width_chars(25)
        self._actualCurrentEncodingEntry.set_width_chars(25)
        actualCurrentEncoding.pack_start(self._actualCurrentEncodingEntry, True, True, 0)
        content.pack_start(actualCurrentEncoding, True, False, 5)

        UTF8Button = Gtk.Button(label=r'Convert to UTF-8')
        UTF8Button.connect(r'clicked', self._toUTF8)
        content.pack_start(UTF8Button, True, True, 5)
        UTF16Button = Gtk.Button(label=r'Convert to UTF-16')
        UTF16Button.connect(r'clicked', self._toUTF16)
        content.pack_start(UTF16Button, True, True, 5)
        UTF32Button = Gtk.Button(label=r'Convert to UTF-32')
        UTF32Button.connect(r'clicked', self._toUTF32)
        content.pack_start(UTF32Button, True, True, 5)
        ASCIIButton = Gtk.Button(label=r'Convert to ASCII (forced)')
        ASCIIButton.connect(r'clicked', self._toASCIIForced)
        content.pack_start(ASCIIButton, True, True, 5)
        self.add(content)
        self.connect(r'delete-event', self._onDestroy)

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _convertEncoding( self, target ):
        encoding = self._actualCurrentEncodingEntry.get_text().strip()
        print("convert from \033[1m" + encoding + "\033[0m to \033[1m" + target + "\033[1m")
        #self.view.metageditActivatable.convertEncoding(self.view.get_buffer(), encoding, target)
        #self.hide()

    def _toUTF8( self, widget ):
        self._convertEncoding(r'utf-8')

    def _toUTF16( self, widget ):
        self._convertEncoding(r'utf-16')

    def _toUTF32( self, widget ):
        self._convertEncoding(r'utf-32')

    def _toASCIIForced( self, widget ):
        self._convertEncoding(r'ascii') #TODO



class SortDialog(Gtk.Window):

    def __init__( self, geditView ):
        Gtk.Window.__init__(self, title=r'Sort',
                                  transient_for=geditView.get_toplevel(),
                                  modal=True,
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
        sortButton = Gtk.Button(label='Do')
        sortButton.connect(r'clicked', self._sort)
        content.pack_start(sortButton, True, True, 5)
        self.add(content)
        self.connect('delete-event', self._onDestroy)

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _setReverse( self, button ):
        self.reverse = button.get_active()

    def _setDedup( self, button ):
        self.dedup = button.get_active()

    def _setCase( self, button ):
        self.case = button.get_active()

    def _sort( self, widget ):
        offset = self._sortOffsetEntry.get_text().strip()
        offset = int(offset) if offset else 0
        self.view.metageditActivatable.sortLines(
                self.view.get_buffer(),
                reverse=self.reverse,
                caseSensitive=self.case,
                dedup=self.dedup,
                offset=offset)
        self.hide()

