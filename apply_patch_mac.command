#!/bin/bash
set -o nounset
# Do not use errexit here

# Roses are red, violets are blue, sugar is sweet, and so are you.
# Enjoy your usual ratio: 5% of lines do the actual work, and the rest are there to make sure they work. (It's like 1%, actually)

WORKINGDIR=$(pwd)
SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPTDIR"
args="$@"

sourcefile='&sourcefile&'
targetfile='&targetfile&'
changes="changes.vcdiff"
olddir="old"

find_xdelta3() {
	chmod +x ./xdelta3_mac 2>/dev/null
	if [ -x ./xdelta3_mac ] && file ./xdelta3_mac | grep -q "Mach-O"; then
		app="./xdelta3_mac"
	elif hash xdelta3 2>/dev/null; then
		app="xdelta3"
	elif hash wine 2>/dev/null && [ -f "xdelta3.exe" ]; then
		app="wine ./xdelta3.exe"
	else
		echo "Error: The required application is not found or inaccessible."
		echo "Please either make sure the file \"xdelta3_mac\" has execute rights, install xdelta3 [recommended], or install WinE."
		cd "$WORKINGDIR"
		return 1
	fi
	return 0
}

find_inputs() {
	found=false
	if [ ! -z "$args" ] && [ ! "$args" = " " ]; then
		if [ -f "$args" ]; then
			sourcefile=$@
			found=true
		else
			echo "Warning: Input file \"$args\" is not found. Ignored."
			found=false
		fi
	fi
	if [ ! -f "$sourcefile" ] && [ $found == false ]; then
		if [ -f "../$sourcefile" ]; then
			sourcefile="../$sourcefile"
			targetfile="../$targetfile"
			olddir="../$olddir"
		else
			echo "Error: Source file not found."
			echo "The file \"$sourcefile\" must be in the same folder as this script."
			cd "$WORKINGDIR"
			return 1
		fi
	fi
	if [ ! -f "$changes" ]; then
		echo "Error: VCDIFF file \"$changes\" is missing."
		echo "Please extract everything from the archive."
		cd "$WORKINGDIR"
		return 1
	fi
	return 0
}

check_target_file() {
	if [ -f "$targetfile" ]; then
		echo "Target file \"$targetfile\" already exists."
		if read -t 5 -p "Continue and overwrite? [y/n]" yn; then
			if [[ $yn != y* ]]; then
				echo "Aborted by user."
				return 1
			fi
		else
			echo "  User didn't answer. Continuing..."
		fi
	fi
	return 0
}

run_patch () {
	echo "Attempting to patch \"$sourcefile\"..."
	`$app -d -f -s "$sourcefile" "$changes" "$targetfile"`
	return 0
}

move_old_file () {
	if [ -f "$targetfile" ]; then
		mkdir -p "$olddir" >/dev/null
		if mv "$sourcefile" "$olddir/"; then
			echo "Moved the old file to directory \"$olddir\"."
		else
			echo "Warning: Couldn't moved the old file."
		fi
		return 0
	fi
	return 0
}

if find_xdelta3 && find_inputs && check_target_file; then
	if run_patch; then
		if ! move_old_file; then
			ignore=1
		fi
		echo "Done."
		cd "$WORKINGDIR"
		return 0 2>/dev/null || exit 0
	else
		echo "Error: Patching wasn't successful!"
	fi
fi

cd "$WORKINGDIR"
return 1 2>/dev/null || exit 1