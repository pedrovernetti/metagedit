# Metagedit

Metagedit is a python plugin for [Gedit](https://en.wikipedia.org/wiki/Gedit) (GNOME Text Editor, usually shipped with Debian, Fedora, openSUSE and Ubuntu) which adds various improvements and functionalities to it.

### Characteristics

* Metagedit-related settings/prefs are all stored using __GSettings__, persisting through Gedit sessions and being externally modifiable via gsettings interfaces;
* __Saved sessions are stored as files__ at a subfolder inside Gedit's config folder, to be easily copied around;
* Most __operations__ work both on the __whole document__ (when nothing is selected) and on __selected parts only__ (when something is).

----
### Features It Adds

* __Color Picker__: adds a better "Pick Color" dialog, accessible via Tools menu;
* __Dark Theme__: adds a toggle at View menu to enable/disable the GTK dark theme for Gedit;
* __Document Statistics__: adds a real-time/self-refreshing "Document Statistics" dialog, accessible via Tools menu;
* __Encoding Utilities__: adds functionalities to better auto-detect or manually set the actual encoding of documents and more, all accessible via context menu (dialog for manually setting encoding allows for previewing the effects), and shows the current encoding on the status bar;
* __Extra/New Keyboard Shortcuts__: adds some extra keyboard shortcuts, like ctrl+Y for undoing, ctrl+E for deleting current line (or selected ones) and ctrl+Tab/ctrl+shift+Tab/ctrl+PageDown/ctrl+PageUp to switch tabs;
* __Line Operations__: adds an improved Sort dialog to Gedit (at Tools menu and context menu) and also some quick linewise sort-like (removing empty lines, sorting, deduplicating, reversing and shuffling) and joining operations to context menu (works both on selections and whole-document-wide);
* __Open as Administrator__: adds a File menu option to re-open file as administrator (Root), making it possible to quikcly edit protected file;
* __Overlay Scrollbar__: adds a toggle at View menu to enable/disable overlay scrollbars for Gedit;
* __Remove Trailing Spaces__: adds a context menu option to remove trailing spaces (incl. trailing newlines when applied to the whole document);
* __Restore Unsaved Documents__: when auto-resuming of previous session is enabled (see _Sessions_ feature), unsaved documents are remembered and restored along with the other tabs;
* __Scroll Past Bottom__: adds a bottom margin to Gedit view, which can be enabled/disable via toggle on View menu;
* __Sessions__: adds a "Sessions" submenu where you can save/load Gedit tab sessions and toggle auto-resuming of previous session on startup (remembering tabs);
* __Smart Home/End/Backspace__: enables the Smart-Home, Smart-End and Smart-Backspace behaviors (pressing Home moves first to the end of indentation, pressing End acts similarly and pressing Backspace on indentations removes as many spaces as needed to remove one indentation level).

----
### Previews

##### Context Menu

![Context Menu](https://github.com/pedrovernetti/metagedit/raw/master/screenshots/context-menu-demo.gif)

##### Sessions Menu and Dialog

![Sessions Menu and Dialog](https://github.com/pedrovernetti/metagedit/raw/master/screenshots/sessions-demo.gif)

##### Switching Themes

![Switching Theme](https://github.com/pedrovernetti/metagedit/raw/master/screenshots/theme-switch-demo.gif)

##### "Edit as Administrator"

!["Edit as Administrator"](https://github.com/pedrovernetti/metagedit/raw/master/screenshots/edit-as-admin-demo.gif)

##### Additional Color Schemes ("Editor Color Themes")

You can find the dark color scheme used in the above previews [here](https://github.com/pedrovernetti/gedit-color-schemes/) (plus 3 others - not all dark).

----
### Installation

##### Using Installer Script

Run: `./install.sh` or, for a re-installation: `./install.sh --reinstall` (no `sudo`).

##### Dependencies

__Metagedit__ depends on the following third-party Python libraries/modules:
 * chardet
 * iso-639

----
### Uninstall

##### Using Installer Script

Run: `./install.sh --uninstall` or, if you want to remove settings and related files, too: `./install.sh --full-uninstall`.

----
### Bugs
If you find a bug, please report it at https://github.com/pedrovernetti/metagedit/issues.

----
### License

__Metagedit__ is distributed under the terms of the GNU General Public License, version 3 (__GPL-3.0__). See the [LICENSE](/LICENSE) file for details.
