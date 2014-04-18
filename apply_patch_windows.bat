@echo off
setlocal
set sourcefile=&sourcefile&
set targetfile=&targetfile&
set app=xdelta3.exe
set changes=changes.vcdiff
set olddir=old

if exist "%~1" (
    set sourcefile=%~1
    goto startnow
)
if not exist "%sourcefile%" (
	if exist "..\%sourcefile%" (
		set "sourcefile=..\%sourcefile%"
		set "targetfile=..\%targetfile%"
		set olddir=..\%olddir%
	) else (goto filenotfound)
)
if not exist "%changes%" goto filenotfound
if not exist "%app%" goto filenotfound

if exist "%targetfile%" (
    echo Target file "%targetfile%" already exists. Press enter to continue and overwrite it, or press Ctrl + C to cancel.
	set /P bla=  
)

:startnow
echo Attempting to patch "%sourcefile%"...
%app% -d -f -s "%sourcefile%" "%changes%" "%targetfile%"
if exist "%targetfile%" (
	mkdir %olddir%
	move "%sourcefile%" %olddir%
	echo Done.
	exit /b
)
echo Error occured! Patching wasn't successful!
PAUSE
exit /b

:filenotfound 
echo The files "%sourcefile%", "%changes%", and "%app%" must be in the same folder as this script!
pause
exit /b
