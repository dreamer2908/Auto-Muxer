#!/bin/bash
cd "$(dirname "$0")"
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
chmod +x ./xdelta3_mac 2>/dev/null
if [ -x ./xdelta3_mac ] && file ./xdelta3_mac | grep -q "Mach-O"; then
    app="./xdelta3_mac"
elif hash xdelta3 2>/dev/null; then
    app="xdelta3"
elif hash wine 2>/dev/null && [ -f "xdelta3.exe" ]; then
    app="wine ./xdelta3.exe"
else
    echo "The required application is not found or inaccessible."
    echo "Please either make sure the file 'xdelta3_mac' has execute rights, install xdelta3 [recommended], or install WinE."
    exit 1
fi
echo "Attempting to patch..."
if [ ! -z "$basefile" ] && [ ! "$basefile" = " " ]; then 
    `$app -d -f -s "$basefile" "$changes"`
else
    `$app -d -f "$changes"`
fi
mkdir -p old && mv "$basefile" ./old/
echo "Done."
exit 0
