#!/bin/bash
basefile="&basefile&"
patchedfile="&patchedfile&"
changes="changes.vcdiff"
args="$@"
if [ -f "$patchedfile" ]; then
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
        basefile=$@
    else
        echo "'$args' is not found"
        read tmp
        exit 1
    fi
elif [ ! -f "$basefile" ] || [ ! -f "$changes" ]; then
    echo "The files '$basefile' and '$changes' must be in the same folder as this script."
    exit 1
fi
chmod +x ./xdelta3 2>/dev/null
chmod +x ./xdelta3.x86_64 2>/dev/null
if [ -x ./xdelta3.x86_64 ] && [ `getconf LONG_BIT` = "64" ] && file ./xdelta3.x86_64 | grep -q "GNU/Linux"; then
    app="./xdelta3.x86_64"
elif [ -x ./xdelta3 ] && file ./xdelta3 | grep -q "GNU/Linux"; then
    app="./xdelta3"
elif hash xdelta3 2>/dev/null; then
    app="xdelta3"
elif hash wine 2>/dev/null && [ -f "xdelta3.exe" ]; then
    app="wine ./xdelta3.exe"
else
    echo "The required application is not found or inaccessible."
    echo "Please either make sure the file 'xdelta3' has execute rights, install xdelta3 [recommended], or install WinE."
    exit 1
fi
echo "Attempting to patch $basefile..."
`$app -d -f -s "$basefile" "$changes" "$patchedfile"`
mkdir -p old && mv "$basefile" ./old/
echo "Done."
exit 0
