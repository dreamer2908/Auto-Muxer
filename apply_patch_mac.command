#!/bin/bash
set -o nounset
set -o errexit
cd "$(dirname "$0")"
sourcefile='&sourcefile&'
targetfile='&targetfile&'
changes="changes.vcdiff"
olddir="old"
args="$@"
if [ ! -z "$args" ] && [ ! "$args" = " " ]; then 
    if [ -f "$args" ]; then 
        sourcefile=$@
    else
        echo "Input file \"$args\" is not found."
        exit 1
    fi
elif [ ! -f "$sourcefile" ]; then
	if [ -f "../$sourcefile" ]; then
		sourcefile="../$sourcefile"
		targetfile="../$targetfile"
		olddir="../$olddir"
	else
		echo "The files \"$sourcefile\" and \"$changes\" must be in the same folder as this script."
		exit 1
	fi
elif [ ! -f "$changes" ]; then
    echo "The files \"$sourcefile\" and \"$changes\" must be in the same folder as this script."
    exit 1
fi
if [ -f "$targetfile" ]; then
	echo "Target file \"$targetfile\" already exists."
	read -p "Press enter to continue and overwrite it, or Ctrl + C to abort the operation." yn
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
    echo "Please either make sure the file \"xdelta3_mac\" is an executable Mac file and has execute rights, install xdelta3 [recommended], or install WinE."
    exit 1
fi
echo "Attempting to patch \"$sourcefile\"..."
`$app -d -f -s "$sourcefile" "$changes" "$targetfile"`
if [ -f "$targetfile" ]; then 
	mkdir -p "$olddir" && mv "$sourcefile" "$olddir/"
fi
echo "Done."
exit 0
