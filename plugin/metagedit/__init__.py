
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
from time import time as nowTime
import gi
gi.require_version(r'Gedit', r'3.0')
gi.require_version(r'Gtk', r'3.0')
from gi.repository import GLib, GObject, Gio, Gtk, GtkSource, Gdk, Gedit

from .textManipulation import *
from .dialogs import *



settings = Gio.Settings.new(r'org.gnome.gedit.plugins.metagedit')
## SESSIONS
sessionsFolder = os.environ[r'HOME'] + r'/.config/gedit/metagedit-sessions/'



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
        if ((fileLocation is None) or (fileLocation.get_uri_scheme() is None)): return False
        elif (r'file' not in fileLocation.get_uri_scheme()): return False
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

    def _closeTabIfJunk( self, tab ):
        if ((tab is None) or (tab.get_state() != 0)): return
        document = tab.get_document()
        if (document.get_file().get_location() is not None): return
        if ((document.can_undo()) or (document.can_redo())): return
        #content = document.get_text(document.get_start_iter(), document.get_end_iter(), False)
        #if (re.match(r'[^\s]', content)): return # tab has some content
        GObject.idle_add(self.window.close_tab, tab)

    def _onActiveTabChange( self, window, tab ):
        ## ENCODING STUFF
        self._updateEncodingStatus(tab.get_document())
        ## OPEN AS ADMIN
        self.window.lookup_action(r'open-as-admin').set_enabled(self._allowOpenAsAdmin())

    def _onActiveTabStateChange( self, window ):
        ## ENCODING STUFF
        if Gedit.TabState.STATE_NORMAL == window.get_active_tab().get_state():
            self._updateEncodingStatus(self.window.get_active_document())
        ## OPEN AS ADMIN
        self.window.lookup_action(r'open-as-admin').set_enabled(self._allowOpenAsAdmin())

    def _onKeyPressEvent( self, window, event ):
        key = Gdk.keyval_name(event.keyval)
        ## EXTRA KEYBOARD SHORTCUTS
        switchKeys = (r'ISO_Left_Tab', r'Page_Up', r'Tab', r'Page_Down')
        if ((event.state & Gdk.ModifierType.CONTROL_MASK) and (key in switchKeys)):
            self._switchTabs(key in switchKeys[:2])

    def _onDocumentSave( self, document, data=None ):
        ## REMOVE TRAILING SPACES
        removeTrailingSpaces(document, True)

    def _onTabAdded( self, window, tab, data=None ):
        tab.get_document().connect(r'save', self._onDocumentSave)
        ## SESSIONS
        if (self._resumedSessionTime > (nowTime() - 2)): self._closeTabIfJunk(tab)
        else: self.saveSession()

    def _onTabRemoved( self, window, tab, data=None ):
        ## SESSIONS
        if (not self._quitting): self.saveSession()

    def _onTabsReordered( self, window, data=None ):
        ## SESSIONS
        self.saveSession()

    def _onWindowShow( self, window, data=None ):
        ## SESSIONS
        if (len(self.window.get_application().get_windows()) == 1):
            if (settings.get_value(r'resume-session').get_boolean()):
                self.loadSession()

    def _onQuit( self, application=None, user_data=None ):
        ## SESSIONS
        self._quitting = True
        if (len(self.window.get_application().get_windows()) == 1):
            self.saveSession()

    def registerSession( self, sessionName ):
        ## SESSIONS
        sessionActionName = r'load-session-' + sessionName.replace(r' ', r'_')
        self._sessionsActions.add(sessionActionName)
        sessionAction = Gio.SimpleAction(name=sessionActionName)
        sessionAction.connect(r'activate', lambda a, p: self.loadSession(sessionName))
        self.window.add_action(sessionAction)

    def saveSession( self, sessionName=None ):
        ## SESSIONS
        if (self.window.get_active_document() is None): return
        tabs = self.window.get_active_tab().get_parent().get_children()
        session = []
        for tab in tabs:
            document = tab.get_document()
            if (document.get_file().get_location() is None): continue
            active = r'x' if (tab == self.window.get_active_tab()) else r' '
            line = str(document.get_iter_at_mark(document.get_insert()).get_line() + 1)
            column = str(document.get_iter_at_mark(document.get_insert()).get_line_offset() + 1)
            encoding = document.get_file().get_encoding()
            encoding = (r' ' * 16) if (encoding is None) else encoding.get_charset().ljust(16, r' ')
            info = active + '\t' + line.ljust(6, r' ') + '\t'
            info += column.ljust(6, r' ') + '\t' + encoding + '\t'
            session.append(info + re.sub(r'^/', r'file:///', document.get_uri_for_display()))
        if (sessionName is None):
            session = [re.sub(r'^(.*?) *(\t.*?) *(\t.*?) *(\t.*?) *(\t.+)$', r'\1\2\3\4\5', entry)
                        for entry in session]
            settings.set_value(r'previous-session', GLib.Variant(r'as', session))
        else:
            try: open(sessionsFolder + sessionName, r'x').write('\n'.join(session))
            except: return
            self.registerSession(sessionName)
            self.window.get_application().metageditActivatable.updateMenuSessions()

    def loadSession( self, sessionName=None ):
        ## SESSIONS
        if (sessionName is None):
            sessionEntries = settings.get_value(r'previous-session').get_strv()
            self._resumedSessionTime = nowTime()
        else:
            try: sessionEntries = open(sessionsFolder + sessionName, r'r').read().splitlines()
            except: return
        openTabs = set()
        if (settings.get_value(r'replace-session-on-load').get_boolean()):
            self.window.close_all_tabs()
        elif (self.window.get_active_tab() is not None):
            for tab in self.window.get_active_tab().get_parent().get_children():
                self._closeTabIfJunk(tab)
            openTabs = self.window.get_active_tab().get_parent().get_children()
            openTabs = [tab.get_document().get_uri_for_display() for tab in openTabs]
            openTabs = set([re.sub(r'^/', r'file:///', tab) for tab in openTabs])
        #if (len(openTabs) == 1): self._closeTabIfJunk(self.window.get_active_tab())
        for entry in sessionEntries:
            active, line, column, encoding, toOpen = tuple(entry.split('\t', 4))
            if (toOpen in openTabs): continue
            active = (active.casefold().strip() in {r'x', r'active', r'true'})
            encoding = encoding.strip()
            if (encoding == r''): encoding = None
            else: encoding = gi.repository.GtkSource.Encoding.get_from_charset(encoding)
            toOpen = Gio.File.new_for_uri(toOpen)
            self.window.create_tab_from_location(
                    toOpen, encoding, int(line), int(column), True, active)

    def removeSession( self, sessionName ):
        ## SESSIONS
        sessionPath = sessionsFolder + sessionName
        if (os.path.isfile(sessionPath)):
            try: os.remove(sessionPath)
            except: return
        self.window.remove_action(r'load-session-' + sessionName.replace(r' ', r'_'))
        self.window.get_application().metageditActivatable.updateMenuSessions()

    def editSession( self, sessionName ):
        ## SESSIONS
        sessionPath = sessionsFolder + sessionName
        try: tabs = self.window.get_active_tab().get_parent().get_children()
        except: tabs = set()
        for tab in tabs:
            if (tab.get_document().get_uri_for_display() == sessionPath):
                self.window.set_active_tab(tab)
                tab.get_document().set_language(None)
                return
        gfile = Gio.File.new_for_uri(r'file://' + sessionPath)
        encoding = gi.repository.GtkSource.Encoding.get_from_charset(r'UTF-8')
        self.window.create_tab_from_location(gfile, encoding, 0, 0, True, True)
        tab = self.window.get_active_tab()
        tab.get_document().set_language(None)

    def do_activate( self ):
        self.window.metageditActivatable = self
        self.handlers = set()
        self.handlers.add(self.window.connect(r'active_tab_changed', self._onActiveTabChange))
        self.handlers.add(self.window.connect(r'active_tab_state_changed', self._onActiveTabStateChange))
        self.handlers.add(self.window.connect(r'show', self._onWindowShow))
        self.handlers.add(self.window.connect(r'delete-event', self._onQuit))
        self.handlers.add(self.window.connect(r'tab-added', self._onTabAdded))
        self.handlers.add(self.window.connect(r'tab-removed', self._onTabRemoved))
        self.handlers.add(self.window.connect(r'tabs-reordered', self._onTabsReordered))
        ## ENCODING STUFF
        self.window.encodingDialog = EncodingDialog(self.window)
        self.window.percentEncodeDialog = PercentEncodeDialog(self.window)
        self._encodingStatusLabel = Gtk.Label(label='\U00002014')
        self.window.get_statusbar().pack_end(self._encodingStatusLabel, False, False, 12)
        self._updateEncodingStatus(self.window.get_active_document())
        encodingAction = Gio.SimpleAction(name=r'encoding-dialog')
        encodingAction.connect(r'activate', lambda a, p: showDialog(self.window.encodingDialog))
        self.window.add_action(encodingAction)
        ## LINE OPERATIONS
        self.window.sortDialog = SortDialog(self.window)
        removeLineAction = Gio.SimpleAction(name=r'remove-line')
        removeLineAction.connect(r'activate', lambda a, p: removeLines(self.window.get_active_document()))
        self.window.add_action(removeLineAction)
        sortAction = Gio.SimpleAction(name=r'sort-dialog')
        sortAction.connect(r'activate', lambda a, p: showDialog(self.window.sortDialog))
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
        ## SESSIONS
        self._resumedSessionTime = 0
        self._quitting = False
        self._sessionsActions = set()
        if (not os.path.isdir(sessionsFolder)):
            try: os.mkdir(sessionsFolder)
            except: pass
        else:
            for session in os.listdir(sessionsFolder): self.registerSession(session)
        saveSessionAction = Gio.SimpleAction(name=r'save-session-auto')
        saveSessionAction.connect(r'activate', lambda a, p: self.saveSession())
        self.window.add_action(saveSessionAction)
        self.window.saveSessionDialog = SaveSessionDialog(self.window, sessionsFolder)
        saveSessionDialogAction = Gio.SimpleAction(name=r'save-session-dialog')
        saveSessionDialogAction.connect(r'activate', lambda a, p: showDialog(self.window.saveSessionDialog))
        self.window.add_action(saveSessionDialogAction)
        self.window.manageSessionsDialog = ManageSessionsDialog(self.window, sessionsFolder)
        manageSessionsDialogAction = Gio.SimpleAction(name=r'manage-sessions-dialog')
        manageSessionsDialogAction.connect(r'activate', lambda a, p: showDialog(self.window.manageSessionsDialog))
        self.window.add_action(manageSessionsDialogAction)
        ## DOCUMENT STATS
        self.window.documentStatsDialog = DocumentStatsDialog(self.window)
        documentStatsDialogAction = Gio.SimpleAction(name=r'document-stats-dialog')
        documentStatsDialogAction.connect(r'activate', lambda a, p: showDialog(self.window.documentStatsDialog))
        self.window.add_action(documentStatsDialogAction)
        ## PICK COLOR
        self.window.pickColorDialog = PickColorDialog(self.window)
        pickColorDialogAction = Gio.SimpleAction(name=r'pick-color-dialog')
        pickColorDialogAction.connect(r'activate', lambda a, p: showDialog(self.window.pickColorDialog))
        self.window.add_action(pickColorDialogAction)
        ## TRANSLATE
        if (translationIsAvailable):
            self.window.translationLanguagesDialog = TranslationLanguagesDialog(self.window)

    def do_deactivate( self ):
        delattr(self.window, r'metageditActivatable')
        for handler in self.handlers: self.window.disconnect(handler)
        ## ENCODING STUFF
        del self.window.encodingDialog
        del self.window.percentEncodeDialog
        Gtk.Container.remove(self.window.get_statusbar(), self._encodingStatusLabel)
        del self._encodingStatusLabel
        ## LINE OPERATIONS
        del self.window.sortDialog
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
        del self.window.saveSessionDialog
        del self.window.manageSessionsDialog
        self.window.remove_action(r'save-session-auto')
        self.window.remove_action(r'save-session-dialog')
        self.window.remove_action(r'manage-sessions-dialog')
        for sessionAction in self._sessionsActions:
            self.window.remove_action(sessionAction)
        ## DOCUMENT STATS
        del self.window.documentStatsDialog
        self.window.remove_action(r'document-stats-dialog')
        ## PICK COLOR
        del self.window.pickColorDialog
        self.window.remove_action(r'pick-color-dialog')
        ## TRANSLATE
        if (translationIsAvailable):
            del self.window.translationLanguagesDialog

    def do_update_state( self ):
        pass



class MetageditViewActivatable(GObject.Object, Gedit.ViewActivatable):
    view = GObject.property(type=Gedit.View)

    def __init__( self ):
        GObject.Object.__init__(self)

    def _addSeparatorToMenu( self, menu, isSubmenu=False ):
        separator = Gtk.SeparatorMenuItem()
        separator.show()
        if (not isSubmenu): self.contextMenuEntries.add(separator)
        menu.append(separator)

    if (translationIsAvailable):
        def _addTranslationToContextMenu( self, menu ):
            ## TRANSLATE
            translationOptions = Gtk.MenuItem.new_with_label("Translate")
            translationOptions.show()
            self.contextMenuEntries.add(translationOptions)
            menu.append(translationOptions)
            translationOptionsSubmenu = Gtk.Menu()
            chooseLanguagesItem = Gtk.MenuItem.new_with_mnemonic("Choose Languages...")
            chooseLanguagesItem.show()
            chooseLanguagesItem.connect(
                    r'activate', lambda i: showDialog(self.window.translationLanguagesDialog))
            translationOptionsSubmenu.append(chooseLanguagesItem)
            self._addSeparatorToMenu(translationOptionsSubmenu, True)
            for code, language in self.window.translationLanguagesDialog.languages.items():
                translateToLanguageItem = Gtk.MenuItem.new_with_mnemonic("to " + language)
                translateToLanguageItem.show()
                translateToLanguageItem.code = code
                translateToLanguageItem.connect(
                        r'activate', lambda i: translate(self.view.get_buffer(), i.code))
                translationOptionsSubmenu.append(translateToLanguageItem)
            translationOptions.set_submenu(translationOptionsSubmenu)

    def _addEncodingOptionsToContextMenu( self, menu ):
        ## ENCODING STUFF
        encodingOptions = Gtk.MenuItem.new_with_label("Encoding")
        encodingOptions.show()
        self.contextMenuEntries.add(encodingOptions)
        menu.append(encodingOptions)
        encodingOptionsSubmenu = Gtk.Menu()
        encodingItem = Gtk.MenuItem.new_with_mnemonic("Manually Set Encoding...")
        encodingItem.show()
        encodingItem.connect(r'activate', lambda i: showDialog(self.window.encodingDialog))
        encodingOptionsSubmenu.append(encodingItem)
        fixEncodingItem = Gtk.MenuItem.new_with_mnemonic("Redetect Encoding")
        fixEncodingItem.show()
        fixEncodingItem.connect(r'activate', lambda i: redecode(self.view.get_buffer()))
        encodingOptionsSubmenu.append(fixEncodingItem)
        self._addSeparatorToMenu(encodingOptionsSubmenu, True)
        self.percentEncodeItem = Gtk.MenuItem.new_with_mnemonic("Percent-Encode")
        self.percentEncodeItem.show()
        self.percentEncodeItem.connect(r'activate', lambda i: percentEncode(self.view.get_buffer()))
        encodingOptionsSubmenu.append(self.percentEncodeItem)
        self.percentEncodeDialogItem = Gtk.MenuItem.new_with_mnemonic("Percent-Encode with Exceptions...")
        self.percentEncodeDialogItem.show()
        self.percentEncodeDialogItem.connect(r'activate', lambda i: showDialog(self.window.percentEncodeDialog))
        encodingOptionsSubmenu.append(self.percentEncodeDialogItem)
        self.percentDecodeItem = Gtk.MenuItem.new_with_mnemonic("Percent-Decode")
        self.percentDecodeItem.show()
        self.percentDecodeItem.connect(r'activate', lambda i: percentDecode(self.view.get_buffer()))
        encodingOptionsSubmenu.append(self.percentDecodeItem)
        encodingOptions.set_submenu(encodingOptionsSubmenu)

    def _addLineOperationsToContextMenu( self, menu ):
        sortOptions = Gtk.MenuItem.new_with_label("Lines")
        sortOptions.show()
        self.contextMenuEntries.add(sortOptions)
        menu.append(sortOptions)
        sortOptionsSubmenu = Gtk.Menu()
        ## COMMENT/UNCOMMENT
        commentItem = Gtk.MenuItem.new_with_mnemonic("Comment")
        commentItem.show()
        commentItem.connect(r'activate', lambda i: commentLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(commentItem)
        uncommentItem = Gtk.MenuItem.new_with_mnemonic("Uncomment")
        uncommentItem.show()
        uncommentItem.connect(r'activate', lambda i: uncommentLines(self.view.get_buffer()))
        sortOptionsSubmenu.append(uncommentItem)
        ## LINE OPERATIONS
        self._addSeparatorToMenu(sortOptionsSubmenu, True)
        sortDialogItem = Gtk.MenuItem.new_with_mnemonic("Advanced Sort...")
        sortDialogItem.show()
        sortDialogItem.connect(r'activate', lambda i: showDialog(self.window.sortDialog))
        sortOptionsSubmenu.append(sortDialogItem)
        self._addSeparatorToMenu(sortOptionsSubmenu, True)
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
        sortDedupItem = Gtk.MenuItem.new_with_mnemonic("Sort and Remove Duplicates")
        sortDedupItem.show()
        sortDedupItem.connect(r'activate', lambda i: sortLines(self.view.get_buffer(), dedup=True))
        sortOptionsSubmenu.append(sortDedupItem)
        sortOptions.set_submenu(sortOptionsSubmenu)

    def _populateContextMenu( self, menu ):
        if (not isinstance(menu, Gtk.MenuShell)): return
        hasSelection = self.view.get_buffer().get_has_selection()
        self._addSeparatorToMenu(menu)
        ## TRANSLATE
        if (translationIsAvailable):
            self._addTranslationToContextMenu(menu)
            self._addSeparatorToMenu(menu)
        ## LINE OPERATIONS
        self._addLineOperationsToContextMenu(menu)
        ## ENCODING STUFF
        self._addEncodingOptionsToContextMenu(menu)
        formattingOptions = Gtk.MenuItem.new_with_label("Formatting")
        formattingOptions.show()
        self.contextMenuEntries.add(formattingOptions)
        menu.append(formattingOptions)
        formattingOptionsSubmenu = Gtk.Menu()
        ## REMOVE TRAILING SPACES
        removeTrailingSpacesItem = Gtk.MenuItem.new_with_mnemonic("Remove Trailing Spaces")
        removeTrailingSpacesItem.show()
        removeTrailingSpacesItem.connect(r'activate', lambda i: removeTrailingSpaces(self.view.get_buffer()))
        formattingOptionsSubmenu.append(removeTrailingSpacesItem)
        formattingOptions.set_submenu(formattingOptionsSubmenu)

    def do_activate( self ):
        self.window = self.view.get_toplevel()
        self.view.metageditActivatable = self
        self.handlers = set()
        self.handlers.add(self.view.connect('populate-popup', lambda v, p: self._populateContextMenu(p)))
        self.contextMenuEntries = set()
        ## BOTTOM MARGIN
        self.view.set_bottom_margin(90)
        ## SMART HOME/END/BACKSPACE
        self._defaultSmartHomeEnd = self.view.get_smart_home_end()
        self.view.set_smart_home_end(GtkSource.SmartHomeEndType.BEFORE)
        self._defaultSmartBackspace = self.view.get_smart_backspace()
        self.view.set_smart_backspace(True)

    def do_deactivate( self ):
        delattr(self.view, r'metageditActivatable')
        for handler in self.handlers: self.view.disconnect(handler)
        for entry in self.contextMenuEntries: entry.destroy()
        del self.contextMenuEntries
        ## SMART HOME/END/BACKSPACE
        self.view.set_smart_home_end(self._defaultSmartHomeEnd)
        self.view.set_smart_backspace(self._defaultSmartBackspace)
        ## COMMENT/UNCOMMENT
        if (hasattr(self.view.get_buffer(), r'lineCommentStyle')):
            delattr(self.view.get_buffer(), r'lineCommentStyle')



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
        settings.set_value(r'prefer-dark-theme', GLib.Variant(r'b', isActive))
        self._settings.set_property(r'gtk-application-prefer-dark-theme', isActive)
        action.set_state(GLib.Variant.new_boolean(isActive))

    def _toggleResumeSession( self, action, state ):
        ## SESSIONS
        isActive = state.get_boolean()
        settings.set_value(r'resume-session', GLib.Variant(r'b', isActive))
        action.set_state(GLib.Variant.new_boolean(isActive))

    def _toggleReplaceCurrentSession( self, action, state ):
        ## SESSIONS
        isActive = state.get_boolean()
        settings.set_value(r'replace-session-on-load', GLib.Variant(r'b', isActive))
        action.set_state(GLib.Variant.new_boolean(isActive))

    def _populateLoadSessionsSection( self ):
        ## SESSIONS
        if (self.loadSessionsSection.get_n_items() > 0): self.loadSessionsSection.remove_all()
        sessions = []
        if (os.path.isdir(sessionsFolder)):
            for session in os.listdir(sessionsFolder):
                if (session.startswith(r'.')): continue
                sessions.append((int(os.path.getmtime(sessionsFolder + session)), session))
            for session in reversed(sorted(sessions)):
                action = r'win.load-session-' + session[1].replace(r' ', r'_')
                label = session[1]
                self.loadSessionsSection.append_item(Gio.MenuItem.new(label, action))

    def updateMenuSessions( self ):
        ## SESSIONS
        self.loadSessionsSection.remove_all()
        self._populateLoadSessionsSection()

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
        darkThemeOn = settings.get_value(r'prefer-dark-theme').get_boolean()
        self._settings.set_property(r'gtk-application-prefer-dark-theme', darkThemeOn)
        toggleDarkThemeAction = Gio.SimpleAction.new_stateful(
                        r'toggle-dark-theme', None, GLib.Variant.new_boolean(darkThemeOn))
        toggleDarkThemeAction.connect(r'change-state', self._toggleDarkTheme)
        self.app.add_action(toggleDarkThemeAction)
        toggleDarkThemeItem = Gio.MenuItem.new("Prefer Dark Theme", r'app.toggle-dark-theme')
        if (Gtk.get_major_version() > 2):
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
        resumeSession = settings.get_value(r'resume-session').get_boolean()
        toggleResumeSessionAction = Gio.SimpleAction.new_stateful(
                        r'toggle-resume-session', None, GLib.Variant.new_boolean(resumeSession))
        toggleResumeSessionAction.connect(r'change-state', self._toggleResumeSession)
        self.app.add_action(toggleResumeSessionAction)
        replaceCurrentSession = settings.get_value(r'replace-session-on-load').get_boolean()
        toggleReplaceCurrentSessionAction = Gio.SimpleAction.new_stateful(
                        r'toggle-replace-current-session', None, GLib.Variant.new_boolean(replaceCurrentSession))
        toggleReplaceCurrentSessionAction.connect(r'change-state', self._toggleReplaceCurrentSession)
        self.app.add_action(toggleReplaceCurrentSessionAction)
        toggleResumeSessionItem = Gio.MenuItem.new("Resume Session on Startup", r'app.toggle-resume-session')
        sessionsSubmenu.append_item(toggleResumeSessionItem)
        replaceSessionItem = Gio.MenuItem.new("Replace Session on Loading", r'app.toggle-replace-current-session')
        sessionsSubmenu.append_item(replaceSessionItem)
        saveSessionItem = Gio.MenuItem.new("Save Current Session", r'win.save-session-dialog')
        sessionsSubmenu.append_item(saveSessionItem)
        manageSessionsItem = Gio.MenuItem.new("Manage Saved Sessions", r'win.manage-sessions-dialog')
        sessionsSubmenu.append_item(manageSessionsItem)
        self.loadSessionsSection = Gio.Menu()
        loadSessionsSectionItem = Gio.MenuItem.new_section("Saved Sessions", self.loadSessionsSection)
        sessionsSubmenuItem.set_section(self.loadSessionsSection)
        self._populateLoadSessionsSection()
        sessionsSubmenu.append_item(loadSessionsSectionItem)
        ## DOCUMENT STATS
        documentStatsDialogItem = Gio.MenuItem.new("Document Statistics", r'win.document-stats-dialog')
        self._toolsMenu.append_menu_item(documentStatsDialogItem)
        ## PICK COLOR
        pickColorDialogItem = Gio.MenuItem.new("Pick Color...", r'win.pick-color-dialog')
        self._toolsMenu.append_menu_item(pickColorDialogItem)

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
        ## SESSIONS
        self.app.remove_action(r'toggle-resume-session')
