
@echo off
setlocal
chcp 65001
set sourcefile=&sourcefile&
set targetfile=&targetfile&
set app=xdelta3.exe
set changes=changes.vcdiff
set sourcefiletmp=sourcefile.tmp
set targetfiletmp=targetfile.tmp
set movesourcefile=0
set movetargetfile=0

if exist "%targetfile%" (
    echo Target file already exists. Press enter to continue and overwrite it, or press Ctrl + C to cancel.
	set /P bla=  
)
if exist "%~1" (
    set sourcefile=%~1
    goto startnow
)
if not exist "%sourcefile%" goto filenotfound
if not exist "%changes%" goto filenotfound
if not exist "%app%" goto filenotfound

:startnow
echo Attempting to patch %sourcefile%...
if %movesourcefile% equ 1 (
	move "%sourcefile%" "%sourcefiletmp%" > nul
) else (
	set sourcefiletmp=%sourcefile%
)
if %movetargetfile% equ 0 set targetfiletmp=%targetfile%
%app% -d -f -s "%sourcefiletmp%" "%changes%" "%targetfiletmp%"
if %movesourcefile% equ 1 move "%sourcefiletmp%" "%sourcefile%" > nul
if %movetargetfile% equ 1 move "%targetfiletmp%" "%targetfile%" > nul
if exist "%targetfile%" (
	mkdir old
	move "%sourcefile%" old
	echo Done.
	exit /b
)
echo Error occured! Patching wasn't successful!
PAUSE
exit /b

:filenotfound 
echo "The files '%sourcefile%', '%changes%', and '%app%' must be in the same folder as this script."
pause
exit /b
