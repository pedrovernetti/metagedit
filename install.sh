#!/bin/bash

tryDoing()
{
    if ! $@; then
        status=$?
        printf "\033[1;31mFAILED!\033[0m\n"
        exit $status
        fi
}

declare -r extensions_folder="/usr/lib/x86_64-linux-gnu/gedit/plugins"
declare -r settings_folder="/usr/share/glib-2.0/schemas"
declare -r settings_schema="org.gnome.gedit.plugins.metagedit"

# get the script's own path
if [[ "$0" != /* ]]; then
    if [[ "$0" == './'* ]]; then declare -r selfpath="$PWD/${0#.\/}"
    elif [[ -f "$PWD/$0" ]]; then declare -r selfpath="$PWD/$0"
    else declare -r selfpath=$(find /bin /sbin /usr/bin /usr/sbin -type f -name '$0' -print 2>/dev/null); fi
else
    declare -r selfpath="$0"
    fi

# take command line arguments
MODE=1
if [[ "$#" -gt 1 ]]; then
    printf "Usage: '$0' [--reinstall|--uninstall|--full-uninstall]\n"
    exit 1
elif [[ "$#" -gt 0 ]]; then
    if [[ "$1" == "--reinstall" ]]; then MODE=2
    elif [[ "$1" == "--full-uninstall" ]]; then MODE=3
    elif [[ "$1" == "--uninstall" ]]; then MODE=4
    else printf "Usage: '$0' [--reinstall|--uninstall|--full-uninstall]\n"; fi
    fi

# default mode's first step (installing dependencies)
if [[ "$MODE" -lt 2 ]]; then
    if [[ $(lsb_release -rs | head -c2) -lt 16 ]]; then
        printf "\033[31;1mOld Ubuntu version (<16.04)...\033[0;0m\n"
        exit
        fi
    printf "\033[1mInstalling dependencies...\033[0m\n"
    tryDoing sudo apt -y install gedit python3-pip python3-gi
    tryDoing sudo apt-get install gir?.?-{glib*,gtk-3.0}
    tryDoing sudo pip3 install chardet iso-639

# non-default modes' first step (removing old files)
else
    sudo rm -vfr "$extensions_folder/metagedit*"
    if [[ "$MODE" -lt 4 ]]; then
        tryDoing rm -vfr "$HOME/.config/gedit/metagedit*"
        tryDoing sudo rm -vfr "$settings_folder/$settings_schema.gschema.xml"
        if [[ "$MODE" -eq 3 ]]; then
            tryDoing sudo glib-compile-schemas /usr/share/glib-2.0/schemas/
            fi
        fi
    if [[ "$MODE" -gt 2 ]]; then
        # finishing
        printf "\033[1;32mDONE!\033[0m\n"
        exit
        fi
    fi

# self-explainatory step
printf "\033[1mCopying the files to the gedit plugins folder...\033[0m\n"
tryDoing sudo mkdir -p "$extensions_folder"
tryDoing sudo cp -rn "${selfpath%/*}/plugin/"* "$extensions_folder"

# adding gsettings entries
printf "\033[1mAdding entries to GSettings...\033[0m\n"
tryDoing sudo cp -n "${selfpath%/*}/$settings_schema.gschema.xml" "$settings_folder/"
tryDoing sudo glib-compile-schemas "$settings_folder/"

# finishing
tryDoing sudo -u "${HOME##*/}" mkdir -p "$HOME/.config/gedit"
printf "\033[1;32mDONE!\033[0m\n"
