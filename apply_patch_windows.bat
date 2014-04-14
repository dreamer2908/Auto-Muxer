@echo off
setlocal
set sourcefile=&sourcefile&
set targetfile=&targetfile&
set app=xdelta3.exe
set changes=changes.vcdiff

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
echo Attempting to patch "%sourcefile%"...
%app% -d -f -s "%sourcefile%" "%changes%" "%targetfile%"
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
echo The files "%sourcefile%", "%changes%", and "%app%" must be in the same folder as this script!
pause
exit /b
