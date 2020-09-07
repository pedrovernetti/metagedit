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

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Set Character Encoding',
                                  transient_for=geditWindow,
                                  resizable=False)
        self.window = geditWindow
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
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



class PercentEncodeDialog(Gtk.Window):

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Percent-Encoding',
                                  transient_for=geditWindow,
                                  resizable=False)
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        self.window = geditWindow
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
        pass

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _encode( self, widget ):
        percentEncode(self.window.get_active_document(), self.ignoreListEntry.get_text())
        self.hide()



## LINE OPERATIONS

class SortDialog(Gtk.Window):

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Sort Lines',
                                  transient_for=geditWindow,
                                  resizable=False)
        self.window = geditWindow
        self.reverse = False
        self.dedup = False
        self.case = False
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
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
        pass

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
        return (int(offset) if re.match(r'^[0-9]+$', offset) else 0)

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

class SaveSessionDialog(Gtk.Window):

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Save Session',
                                  transient_for=geditWindow,
                                  resizable=False)
        self.window = geditWindow
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
        self.sessionNameEntry.set_text(self.window.metageditActivatable.suggestedSessionName())

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _saveSession( self, widget ):
        self.window.metageditActivatable.saveSession(self.sessionNameEntry.get_text())
        self.hide()



class ManageSessionsDialog(Gtk.Window): #TODO

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Save Session',
                                  transient_for=geditWindow,
                                  resizable=False)
        self.window = geditWindow
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
        self.sessionNameEntry.set_text(self.window.metageditActivatable.suggestedSessionName())

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

    def _saveSession( self, widget ):
        self.window.metageditActivatable.saveSession(self.sessionNameEntry.get_text())
        self.hide()



## PICK COLOR

class PickColorDialog(Gtk.Window):

    def __init__( self, geditWindow ):
        Gtk.Window.__init__(self, title=r'Pick Color',
                                  transient_for=geditWindow,
                                  resizable=False)
        self.window = geditWindow
        self.useAlpha = False
        self.uppercaseHex = False
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content.set_border_width(10)
        toggles = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        alphaToggle = Gtk.CheckButton(active=False, label=r'Use Alpha Channel')
        alphaToggle.connect(r'toggled', self._setAlpha)
        toggles.pack_start(alphaToggle, True, False, 0)
        uppercaseHexToggle = Gtk.CheckButton(active=False, label=r'Uppercase Hex Code')
        uppercaseHexToggle.connect(r'toggled', self._setUppercaseHex)
        toggles.pack_start(uppercaseHexToggle, True, False, 0)
        content.pack_start(toggles, True, False, 10)
        self.colorPicker = Gtk.ColorChooserWidget(show_editor=True)
        self.colorPicker.set_use_alpha(False)
        content.pack_start(self.colorPicker, True, True, 5)
        CMYKScaleRow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        CMYKScaleLabel = Gtk.Label(label='CMYK Scale:')
        CMYKScaleRow.pack_start(CMYKScaleLabel, False, True, 10)
        self.CMYKScaleEntry = Gtk.Entry(text=r'100')
        self.CMYKScaleEntry.set_tooltip_text(r'CMYK Scale')
        self.CMYKScaleEntry.set_max_length(4)
        self.CMYKScaleEntry.set_alignment(1.0)
        CMYKScaleRow.pack_start(self.CMYKScaleEntry, True, True, 5)
        content.pack_start(CMYKScaleRow, True, True, 10)
        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        buttonsGroup = Gtk.SizeGroup(mode=Gtk.SizeGroupMode.HORIZONTAL)
        PickHexButton = Gtk.Button(label=r'Hex Code')
        PickHexButton.connect(r'clicked', self._pickHex)
        buttons.pack_start(PickHexButton, True, True, 5)
        buttonsGroup.add_widget(PickHexButton)
        PickRGBButton = Gtk.Button(label=r'RGB(A) Tuple')
        PickRGBButton.connect(r'clicked', self._pickRGB)
        buttons.pack_start(PickRGBButton, True, True, 5)
        buttonsGroup.add_widget(PickRGBButton)
        PickCMYKButton = Gtk.Button(label=r'CMYK Tuple')
        PickCMYKButton.connect(r'clicked', self._pickCMYK)
        buttons.pack_start(PickCMYKButton, True, True, 5)
        buttonsGroup.add_widget(PickCMYKButton)
        content.pack_start(buttons, True, True, 5)
        self.add(content)
        self.connect(r'show', self._onShow)
        self.connect(r'delete-event', self._onDestroy)
        self.colorPicker.grab_focus()

    def _onShow( self, widget=None, event=None ):
        pass

    def _onDestroy( self, widget=None, event=None ):
        self.hide()
        return True

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
