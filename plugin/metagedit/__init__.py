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

import os
from datetime import datetime
import gi
gi.require_version('Gedit', '3.0')
from gi.repository import GLib, GObject, Gio, Gtk, Gdk, Gedit

from .textManipulation import *
from .dialogs import *



class MetageditWindowActivatable(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    def __init__( self ):
        GObject.Object.__init__(self)

    def _isPlainText( self, document ):
        return (document.get_language() is None)

    def _updateEncodingStatus( self, document ):
        ## ENCODING STUFF
        if (document and document.get_file().get_encoding() is not None):
            self._encodingStatusLabel.set_label(document.get_file().get_encoding().get_charset())
            self._encodingStatusLabel.show()
        else:
            self._encodingStatusLabel.hide()

    def _allowOpenAsAdmin( self ):
        ## OPEN AS ADMIN
        if (self.window.get_active_document() is None): return False
        fileLocation = self.window.get_active_document().get_file().get_location()
        if (fileLocation is None): return False # can't re-open if it was deleted or not yet created
        elif (r'admin' in fileLocation.get_uri_scheme()): return False # already "as admin"
        else: return True

    def _openAsAdmin( self, action, data ):
        ## OPEN AS ADMIN
        document = self.window.get_active_document()
        encoding = document.get_file().get_encoding()
        gfile = Gio.File.new_for_uri(r'admin://' + document.get_uri_for_display())
        if (not (document.can_undo() or document.can_redo())):
            self.window.close_tab(self.window.get_active_tab())
        self.window.create_tab_from_location(gfile, encoding, 0, 0, False, True)

    def _switchTabs( self, forward=True ):
        ## EXTRA KEYBOARD SHORTCUTS
        tabs = self.window.get_active_tab().get_parent().get_children()
        tabCount = len(tabs)
        i = 0
        for tab in tabs:
            if (tab == self.window.get_active_tab()): break
            i += 1
        i += -1 if forward else 1
        if (i < 0): i = tabCount - 1
        elif (i >= tabCount): i = 0
        self.window.set_active_tab(tabs[i])

    def _onActiveTabChange( self, window, tab ):
        ## ENCODING STUFF
        self._updateEncodingStatus(tab.get_document())
        ## OPEN AS ADMIN
        self.window.lookup_action('open-as-admin').set_enabled(self._allowOpenAsAdmin())

    def _onActiveTabStateChange( self, window ):
        ## ENCODING STUFF
        if Gedit.TabState.STATE_NORMAL == window.get_active_tab().get_state():
            self._updateEncodingStatus(self.window.get_active_document())
        ## OPEN AS ADMIN
        self.window.lookup_action('open-as-admin').set_enabled(self._allowOpenAsAdmin())

    def _onKeyPressEvent( self, window, event ):
        key = Gdk.keyval_name(event.keyval)
        switchKeys = (r'ISO_Left_Tab', r'Page_Up', r'Tab', r'Page_Down')
        if ((event.state & Gdk.ModifierType.CONTROL_MASK) and (key in switchKeys)):
            self._switchTabs(key in switchKeys[:2])

    def _onDocumentSave( self, document, data=None ):
        ## REMOVE TRAILING SPACES
        removeTrailingSpaces(document, True)

    def _onTabAdded( self, window, tab, data=None ):
        tab.get_document().connect(r'save', self._onDocumentSave)

    def saveSession( self, sessionName=r'._autosavedSession_' ):
        ## SESSIONS
        if (self.window.get_active_document() is None): return
        tabs = self.window.get_active_tab().get_parent().get_children()
        session = [datetime.now().strftime(r'%Y%m%d%H%M%S')]
        for tab in tabs:
            document = tab.get_document()
            if (document.get_file().get_location() is None): continue
            active = r'True' if (tab == self.window.get_active_tab()) else r'False'
            line = str(document.get_iter_at_mark(document.get_insert()).get_line() + 1)
            column = str(document.get_iter_at_mark(document.get_insert()).get_line_offset() + 1)
            encoding = document.get_file().get_encoding()
            encoding = r'' if (encoding is None) else encoding.get_charset()
            info = active + '\t' + line + '\t' + column + '\t' + encoding + '\t'
            session.append(info + document.get_uri_for_display())
        try: open(self._sessionsFolder + sessionName, r'w').write('\n'.join(session))
        except: pass

    def suggestedSessionName( self ):
        ## SESSIONS
        name = self.window.get_active_document().get_short_name_for_display()
        return (name + datetime.now().strftime(r' [%Y-%m-%d %H-%M-%S]'))

    def loadSession( self, sessionName=r'._autosavedSession_' ):
        ## SESSIONS
        if (not os.path.isdir(self._sessionsFolder)): return
        tabs = self.window.get_active_tab().get_parent().get_children()
        openTabPaths = set([tab.get_document().get_uri_for_display() for tab in tabs])
        try:
            sessionEntries = open(self._sessionsFolder + sessionName, r'r').read().splitlines()
            for entry in sessionEntries[1:]:
                active, line, column, encoding, toOpen = tuple(entry.split('\t', 4))
                if (toOpen in openTabPaths): continue
                if (encoding == r''): encoding = None
                else: encoding = gi.repository.GtkSource.Encoding.get_from_charset(encoding)
                toOpen = Gio.File.new_for_path(toOpen)
                self.window.create_tab_from_location(
                        toOpen, encoding, int(line), int(column), True, (active == r'True'))
        except:
            pass

    def do_activate( self ):
        self.window.metageditActivatable = self
        self.handlers = set()
        self.handlers.add(self.window.connect(r'active_tab_changed', self._onActiveTabChange))
        self.handlers.add(self.window.connect(r'active_tab_state_changed', self._onActiveTabStateChange))
        ## ENCODING STUFF
        encodingDialog.setMainWindow(self.window)
        percentEncodeDialog.setMainWindow(self.window)
        self._encodingStatusLabel = Gtk.Label(label='\U00002014')
        self.window.get_statusbar().pack_end(self._encodingStatusLabel, False, False, 12)
        self._updateEncodingStatus(self.window.get_active_document())
        encodingAction = Gio.SimpleAction(name=r'encoding-dialog')
        encodingAction.connect(r'activate', lambda a, p: showDialog(encodingDialog))
        self.window.add_action(encodingAction)
        ## LINE OPERATIONS
        sortDialog.setMainWindow(self.window)
        removeLineAction = Gio.SimpleAction(name=r'remove-line')
        removeLineAction.connect(r'activate', lambda a, p: removeLines(self.window.get_active_document()))
        self.window.add_action(removeLineAction)
        sortAction = Gio.SimpleAction(name=r'sort-dialog')
        sortAction.connect(r'activate', lambda a, p: showDialog(sortDialog))
        self.window.add_action(sortAction)
        shuffleAction = Gio.SimpleAction(name=r'shuffle')
        shuffleAction.connect(r'activate', lambda a, p: shuffleLines(self.window.get_active_document()))
        self.window.add_action(shuffleAction)
        ## EXTRA KEYBOARD SHORTCUTS
        self.handlers.add(self.window.connect(r'key-press-event', self._onKeyPressEvent))
        switchTabNextAction = Gio.SimpleAction(name=r'switch-tab-next')
        switchTabNextAction.connect(r'activate', lambda a, p: self._switchTabs(True))
        self.window.add_action(switchTabNextAction)
        switchTabPreviousAction = Gio.SimpleAction(name=r'switch-tab-previous')
        switchTabPreviousAction.connect(r'activate', lambda a, p: self._switchTabs(False))
        self.window.add_action(switchTabPreviousAction)
        ## OPEN AS ADMIN
        openAsAdminAction = Gio.SimpleAction(name=r'open-as-admin')
        openAsAdminAction.connect(r'activate', self._openAsAdmin)
        self.window.add_action(openAsAdminAction)
        ## REMOVE TRAILING SPACES
        self.handlers.add(self.window.connect(r'tab-added', self._onTabAdded))
        ## SESSIONS
        self._sessionsFolder = os.environ[r'HOME'] + r'/.config/gedit/metagedit-sessions/'
        self._sessionsActions = set()
        if (not os.path.isdir(self._sessionsFolder)):
            try: os.mkdir(self._sessionsFolder)
            except: pass
        else:
            for session in os.listdir(self._sessionsFolder):
                try: sessionID = open(self._sessionsFolder + session, 'r').read(14)
                except: continue
                actionName = r'load-session-' + sessionID
                self._sessionsActions.add(actionName)
                sessionAction = Gio.SimpleAction(name=actionName)
                sessionAction.connect(r'activate', lambda a, p: self.loadSession(session))
                self.window.add_action(sessionAction)
        saveSessionAction = Gio.SimpleAction(name=r'save-session-auto')
        saveSessionAction.connect(r'activate', lambda a, p: self.saveSession())
        self.window.add_action(saveSessionAction)
        saveSessionDialog.setMainWindow(self.window)
        saveSessionDialogAction = Gio.SimpleAction(name=r'save-session-dialog')
        saveSessionDialogAction.connect(r'activate', lambda a, p: showDialog(saveSessionDialog))
        self.window.add_action(saveSessionDialogAction)
        manageSessionsDialog.setMainWindow(self.window)

    def do_deactivate( self ):
        delattr(self.window, r'metageditActivatable')
        for handler in self.handlers: self.window.disconnect(handler)
        ## ENCODING STUFF
        del encodingDialog
        del percentEncodeDialog
        Gtk.Container.remove(self.window.get_statusbar(), self._encodingStatusLabel)
        del self._encodingStatusLabel
        ## LINE OPERATIONS
        del sortDialog
        self.window.remove_action(r'encoding-dialog')
        self.window.remove_action(r'remove-line')
        self.window.remove_action(r'sort-dialog')
        self.window.remove_action(r'shuffle')
        ## EXTRA KEYBOARD SHORTCUTS
        self.window.remove_action(r'switch-tab-next')
        self.window.remove_action(r'switch-tab-previous')
        ## OPEN AS ADMIN
        self.window.remove_action(r'open-as-admin')
        ## SESSIONS
        del saveSessionDialog
        del manageSessionsDialog
        self.window.remove_action(r'save-session-auto')
        self.window.remove_action(r'save-session-dialog')
        for sessionAction in self._sessionsActions:
            self.window.remove_action(sessionAction)

    def do_update_state( self ):
        activeDocument = self.window.get_active_document()
        hasSelection = False if (activeDocument is None) else activeDocument.get_has_selection()
        activeView = self.window.get_active_view()
        if (activeView and hasattr(activeView, r'metageditActivatable')):
            pass #TODO: how to deactivate items on no selection?
            #activeView.metageditActivatable.percentEncodeItem.set_enabled(hasSelection)
            #activeView.metageditActivatable.percentEncodeDialogItem.set_enabled(hasSelection)



class MetageditViewActivatable(GObject.Object, Gedit.ViewActivatable):
    view = GObject.property(type=Gedit.View)

    def __init__( self ):
        GObject.Object.__init__(self)

    def _populateContextMenu( self, view, popup ):
        if (not isinstance(popup, Gtk.MenuShell)): return
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        self.contextMenuEntries.add(separator)
        popup.append(separator)
        sortOptions = Gtk.MenuItem.new_with_label("Lines")
        sortOptions.show()
        ## ENCODING STUFF
        encodingOptions = Gtk.MenuItem.new_with_label("Encoding")
        encodingOptions.show()
        self.contextMenuEntries.add(encodingOptions)
        popup.append(encodingOptions)
        encodingOptionsSubmenu = Gtk.Menu()
        encodingItem = Gtk.MenuItem.new_with_mnemonic("Manually Set Encoding...")
        encodingItem.show()
        encodingItem.connect(r'activate', lambda i: showDialog(encodingDialog))
        encodingOptionsSubmenu.append(encodingItem)
        fixEncodingItem = Gtk.MenuItem.new_with_mnemonic("Redetect Encoding")
        fixEncodingItem.show()
        fixEncodingItem.connect(r'activate', lambda i: redecode(self.view.get_buffer()))
        encodingOptionsSubmenu.append(fixEncodingItem)
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        encodingOptionsSubmenu.append(separator)
        self.percentEncodeItem = Gtk.MenuItem.new_with_mnemonic("Percent-Encode")
        self.percentEncodeItem.show()
        self.percentEncodeItem.connect(r'activate', lambda i: percentEncode(self.view.get_buffer()))
        encodingOptionsSubmenu.append(self.percentEncodeItem)
        self.percentEncodeDialogItem = Gtk.MenuItem.new_with_mnemonic("Percent-Encode with Exceptions...")
        self.percentEncodeDialogItem.show()
        self.percentEncodeDialogItem.connect(r'activate', lambda i: showDialog(percentEncodeDialog))
        encodingOptionsSubmenu.append(self.percentEncodeDialogItem)
        encodingOptions.set_submenu(encodingOptionsSubmenu)
        ## LINE OPERATIONS
        self.contextMenuEntries.add(sortOptions)
        popup.append(sortOptions)
        sortOptionsSubmenu = Gtk.Menu()
        sortDialogItem = Gtk.MenuItem.new_with_mnemonic("Advanced Sort...")
        sortDialogItem.show()
        sortDialogItem.connect(r'activate', lambda i: showDialog(sortDialog))
        sortOptionsSubmenu.append(sortDialogItem)
        joinItem = Gtk.MenuItem.new_with_mnemonic("Join")
        joinItem.show()
        joinItem.connect(r'activate', lambda i: joinLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(joinItem)
        dedupItem = Gtk.MenuItem.new_with_mnemonic("Remove Duplicates")
        dedupItem.show()
        dedupItem.connect(r'activate', lambda i: dedupLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(dedupItem)
        removeEmptyItem = Gtk.MenuItem.new_with_mnemonic("Remove Empty Ones")
        removeEmptyItem.show()
        removeEmptyItem.connect(r'activate', lambda i: removeEmptyLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(removeEmptyItem)
        reverseItem = Gtk.MenuItem.new_with_mnemonic("Reverse")
        reverseItem.show()
        reverseItem.connect(r'activate', lambda i: reverseLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(reverseItem)
        shuffleItem = Gtk.MenuItem.new_with_mnemonic("Shuffle")
        shuffleItem.show()
        shuffleItem.connect(r'activate', lambda i: shuffleLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(shuffleItem)
        sortItem = Gtk.MenuItem.new_with_mnemonic("Sort")
        sortItem.show()
        sortItem.connect(r'activate', lambda i: sortLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(sortItem)
        sortOptions.set_submenu(sortOptionsSubmenu)
        ## REMOVE TRAILING SPACES
        formattingOptions = Gtk.MenuItem.new_with_label("Formatting")
        formattingOptions.show()
        self.contextMenuEntries.add(formattingOptions)
        popup.append(formattingOptions)
        formattingOptionsSubmenu = Gtk.Menu()
        removeTrailingSpacesItem = Gtk.MenuItem.new_with_mnemonic("Remove Trailing Spaces")
        removeTrailingSpacesItem.show()
        removeTrailingSpacesItem.connect(r'activate', lambda i: removeTrailingSpaces(view.get_buffer()))
        formattingOptionsSubmenu.append(removeTrailingSpacesItem)
        formattingOptions.set_submenu(formattingOptionsSubmenu)

    def do_activate( self ):
        self.window = self.view.get_toplevel() # deglobalize dialogs
        self.view.metageditActivatable = self
        self.handlers = set()
        self.handlers.add(self.view.connect('populate-popup', self._populateContextMenu))
        self.contextMenuEntries = set()
        ## BOTTOM MARGIN
        self.view.set_bottom_margin(90)

    def do_deactivate( self ):
        delattr(self.view, r'metageditActivatable')
        for handler in self.handlers: self.view.disconnect(handler)
        for entry in self.contextMenuEntries: entry.destroy()
        del self.contextMenuEntries



class MetageditAppActivatable(GObject.Object, Gedit.AppActivatable):
    app = GObject.property(type=Gedit.App)

    def __init__( self ):
        GObject.Object.__init__(self)
        ## DARK THEME SWITCH
        self._settings = Gtk.Settings.get_default()

    def _setKeyboardShortcut( self, action, shortcut ):
        ## EXTRA KEYBOARD SHORTCUTS
        self.app.remove_accelerator(action, None)
        self.app.set_accels_for_action(action, [shortcut])

    def _clearKeyboardShortcut( self, action ):
        ## EXTRA KEYBOARD SHORTCUTS
        self.app.remove_accelerator(action, None)
        self.app.set_accels_for_action(action, ())

    def _toggleBottomMargin( self, action, state ):
        ## BOTTOM MARGIN
        isActive = state.get_boolean()
        for view in self.app.get_views(): view.set_bottom_margin(90 if isActive else 0)
        action.set_state(GLib.Variant.new_boolean(isActive))

    def _toggleDarkTheme( self, action, state ):
        ## DARK THEME SWITCH
        isActive = state.get_boolean()
        try:
            open(self._darkThemePrefsFile, r'w').write(str(isActive))
            self._settings.set_property(r'gtk-application-prefer-dark-theme', isActive)
            action.set_state(GLib.Variant.new_boolean(isActive))
        except:
            pass

    def do_activate( self ):
        self.app.metageditActivatable = self
        self._fileMenu = self.extend_menu(r'file-section')
        self._file2Menu = self.extend_menu(r'file-section-1')
        self._editMenu = self.extend_menu(r'edit-section')
        self._viewMenu = self.extend_menu(r'view-section')
        self._view2Menu = self.extend_menu(r'view-section-2')
        self._toolsMenu = self.extend_menu(r'tools-section')
        self._documentsMenu = self.extend_menu(r'documents-section')
        ## OPEN AS ADMIN
        openAsAdminItem = Gio.MenuItem.new("Edit as Administrator...", r'win.open-as-admin')
        self._file2Menu.prepend_menu_item(openAsAdminItem)
        ## ENCODING STUFF
        encodingItem = Gio.MenuItem.new("Manually Set Character Encoding...", r'win.encoding-dialog')
        self._toolsMenu.prepend_menu_item(encodingItem)
        ## LINE OPERATIONS
        sortDialogItem = Gio.MenuItem.new("Sort Lines...", r'win.sort-dialog')
        self._toolsMenu.prepend_menu_item(sortDialogItem)
        ## BOTTOM MARGIN
        toggleBottomMarginAction = Gio.SimpleAction.new_stateful(
                        r'toggle-bottom-margin', None, GLib.Variant.new_boolean(True))
        toggleBottomMarginAction.connect(r'change-state', self._toggleBottomMargin)
        self.app.add_action(toggleBottomMarginAction)
        toggleBottomMarginItem = Gio.MenuItem.new("Show Virtual Space at Bottom", r'app.toggle-bottom-margin')
        self._view2Menu.append_menu_item(toggleBottomMarginItem)
        ## DARK THEME SWITCH
        self._originalThemeSettings = self._settings.get_property(r'gtk-application-prefer-dark-theme')
        self._darkThemePrefsFile = os.environ[r'HOME'] + r'/.config/gedit/metagedit-dark-theme'
        darkThemeOn = False
        if (os.path.isfile(self._darkThemePrefsFile)):
            try: darkThemeOn = (open(self._darkThemePrefsFile, r'r').read() == r'True')
            except: pass
        self._settings.set_property(r'gtk-application-prefer-dark-theme', darkThemeOn)
        toggleDarkThemeAction = Gio.SimpleAction.new_stateful(
                        r'toggle-dark-theme', None, GLib.Variant.new_boolean(darkThemeOn))
        toggleDarkThemeAction.connect(r'change-state', self._toggleDarkTheme)
        self.app.add_action(toggleDarkThemeAction)
        toggleDarkThemeItem = Gio.MenuItem.new("Prefer Dark Theme", r'app.toggle-dark-theme')
        if (Gtk.get_major_version() > 2): # a way found to test newer gedit interfaces
            self._viewMenu.prepend_menu_item(toggleDarkThemeItem)
        ## EXTRA KEYBOARD SHORTCUTS
        self._setKeyboardShortcut(r'win.redo', r'<Primary>Y')
        self._setKeyboardShortcut(r'win.goto-line', r'<Primary>G')
        self._setKeyboardShortcut(r'win.find-next', r'<Primary><Shift>F')
        self._setKeyboardShortcut(r'win.remove-line', r'<Primary>E')
        self._clearKeyboardShortcut(r'app.quit')
        ## SESSIONS
        sessionsSubmenu = Gio.Menu()
        sessionsSubmenuItem = Gio.MenuItem.new_submenu("Sessions", sessionsSubmenu)
        if (self._documentsMenu is not None):
            self._documentsMenu.prepend_menu_item(sessionsSubmenuItem)
        else:
            self._fileMenu.append_menu_item(sessionsSubmenuItem)
        saveSessionItem = Gio.MenuItem.new("Save Current Session", r'win.save-session-dialog')
        sessionsSubmenu.append_item(saveSessionItem)
        #TODO: "Continue from Last Session [ ]", "Replace Current Session on Loading [ ]"
        sessionsFolder = os.environ[r'HOME'] + r'/.config/gedit/metagedit-sessions/'
        if (os.path.isdir(sessionsFolder)):
            for session in os.listdir(sessionsFolder):
                try: sessionID = open(sessionsFolder + session, 'r').read(14)
                except: continue
                itemText = "Load \"" + session + "\" Session"
                itemAction = r'win.load-session-' + sessionID
                sessionsSubmenu.append_item(Gio.MenuItem.new(itemText, itemAction))

    def do_deactivate( self ):
        delattr(self.app, r'metageditActivatable')
        del self._fileMenu
        del self._file2Menu
        del self._editMenu
        del self._viewMenu
        del self._view2Menu
        del self._toolsMenu
        del self._documentsMenu
        ## BOTTOM MARGIN
        for view in self.app.get_views(): view.set_bottom_margin(0)
        self.app.remove_action(r'toggle-bottom-margin')
        ## DARK THEME SWITCH
        self._settings.set_property(r'gtk-application-prefer-dark-theme', self._originalThemeSettings)
        self.app.remove_action(r'toggle-dark-theme')
        ## EXTRA KEYBOARD SHORTCUTS
        self._clearKeyboardShortcut(r'win.redo')
        self._clearKeyboardShortcut(r'win.goto-line')
        self._clearKeyboardShortcut(r'win.find-next')
        self._clearKeyboardShortcut(r'win.remove-line')
        self._setKeyboardShortcut(r'app.quit', r'<Primary>Q')
