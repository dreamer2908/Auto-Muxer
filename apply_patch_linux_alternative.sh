#!/bin/bash
basefile=""
changes="changes.vcdiff"
args="$@"
if [ ! -z "$args" ] && [ ! "$args" = " " ]; then 
    if [ -f "$args" ]; then 
        basefile=$@
    else
        echo "'$args' is not found"
    fi
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
if [ ! -z "$basefile" ] && [ ! "$basefile" = " " ]; then 
    `$app -d -f -s "$basefile" "$changes"`
else
    `$app -d -f "$changes"`
fi
echo "Done."
exit 0
