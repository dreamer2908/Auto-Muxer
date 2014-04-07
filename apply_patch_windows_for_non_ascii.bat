
@echo off
setlocal
chcp 65001
set basefile=&basefile&
set patchedfile=&patchedfile&
set app=xdelta3.exe
set changes=changes.vcdiff
set basefiletmp=basefile.tmp
set patchedfiletmp=patchedfile.tmp
set movebasefile=0
set movepatchedfile=0

if exist "%patchedfile%" (
    echo Target file already exists. Press enter to continue and overwrite it, or press Ctrl + C to cancel.
	set /P bla=  
)
if exist "%~1" (
    set basefile=%~1
    goto startnow
)
if not exist "%basefile%" goto filenotfound
if not exist "%changes%" goto filenotfound
if not exist "%app%" goto filenotfound

:startnow
echo Attempting to patch %basefile%...
if %movebasefile% equ 1 (
	move "%basefile%" "%basefiletmp%" > nul
) else (
	set basefiletmp=%basefile%
)
if %movepatchedfile% equ 0 set patchedfiletmp=%patchedfile%
%app% -d -f -s "%basefiletmp%" "%changes%" "%patchedfiletmp%"
if %movebasefile% equ 1 move "%basefiletmp%" "%basefile%" > nul
if %movepatchedfile% equ 1 move "%patchedfiletmp%" "%patchedfile%" > nul
if exist "%patchedfile%" (
	mkdir old
	move "%basefile%" old
	echo Done.
	exit /b
)
echo Error occured! Patching wasn't successful!
PAUSE
exit /b

:filenotfound 
echo "The files '%basefile%', '%changes%', and '%app%' must be in the same folder as this script."
pause
exit /b
