#!/bin/bash
cd "$(dirname "$0")"
sourcefile='&sourcefile&'
targetfile='&targetfile&'
changes="changes.vcdiff"
args="$@"
if [ -f "$targetfile" ]; then
    echo "Target file already exists. Continue and overwrite? [y/n]"
    read -t 5 choice 2>/dev/null
    if [ "$?" -ne "0" ]; then
        echo "User didn't answer. Continuing..."
    elif [[ $choice != y* ]]; then
        echo "Aborted by user."
        exit 0
    fi
fi
if [ ! -z "$args" ] && [ ! "$args" = " " ]; then 
    if [ -f "$args" ]; then 
        sourcefile=$@
    else
        echo "'$args' is not found"
        read tmp
        exit 1
    fi
elif [ ! -f "$sourcefile" ] || [ ! -f "$changes" ]; then
    echo "The files '$sourcefile' and '$changes' must be in the same folder as this script."
    exit 1
fi
chmod +x ./xdelta3_mac 2>/dev/null
if [ -x ./xdelta3_mac ] && file ./xdelta3_mac | grep -q "Mach-O"; then
    app="./xdelta3_mac"
elif hash xdelta3 2>/dev/null; then
    app="xdelta3"
elif hash wine 2>/dev/null && [ -f "xdelta3.exe" ]; then
    app="wine ./xdelta3.exe"
else
    echo "The required application is not found or inaccessible."
    echo "Please either make sure the file 'xdelta3_mac' is an executable Mac file and has execute rights, install xdelta3 [recommended], or install WinE."
    exit 1
fi
echo "Attempting to patch $sourcefile..."
`$app -d -f -s "$sourcefile" "$changes" "$targetfile"`
if [ -f "$targetfile" ]; then 
	mkdir -p old && mv "$sourcefile" ./old/
fi
echo "Done."
exit 0
