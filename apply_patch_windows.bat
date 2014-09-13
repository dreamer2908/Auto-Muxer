@echo off
setlocal

rem Roses are red, violets are blue, sugar is sweet, and so are you.
rem Enjoy your usual ratio: 5% of lines do the actual work, and the rest are there to make sure they work. (It's like 1%, actually)

set sourcefile=&sourcefile&
set targetfile=&targetfile&
set app=xdelta3.exe
set changes=changes.vcdiff
set olddir=old
set WORKINGDIR=%CD%
chdir /d %~dp0
(call )

call :find_xdelta3 && call :find_inputs && call :check_target_file && call :run_patch
call :gtfo
goto :eof

:find_xdelta3
(call)
if exist "%changes%" (
	(call )
) else (
	echo The required application "%app%" can't be found!
)
goto :eof

:find_inputs
(call)
if exist "%~1" (
    set sourcefile=%~1
	(call )
)
if not exist "%sourcefile%" (
	if exist "..\%sourcefile%" (
		set "sourcefile=..\%sourcefile%"
		set "targetfile=..\%targetfile%"
		set "olddir=..\%olddir%"
		(call )
	) else (
		if exist "..\..\%sourcefile%" (
			set "sourcefile=..\..\%sourcefile%"
			set "targetfile=..\..\%targetfile%"
			set "olddir=..\..\%olddir%"
			(call )
		) else ( 
			if exist "..\..\..\%sourcefile%" (
				set "sourcefile=..\..\..\%sourcefile%"
				set "targetfile=..\..\..\%targetfile%"
				set "olddir=..\..\..\%olddir%"
				(call )
			) else ( 
				echo Error: Source file "%sourcefile%" not found.
				echo You must put it in the same folder as this script.
				(call)
			)
		)
	)
) else (
	(call )
)
if not exist "%changes%" (
	echo Error: VCDIFF file \"$changes\" is missing.
	echo Please extract everything from the archive.
	(call)
)
goto :eof

:check_target_file
if exist "%targetfile%" (
    echo Target file "%targetfile%" already exists.
	choice /c yn /t 5 /d y /m "Continue and overwrite"
	if errorlevel 2 (
		echo Aborted by user.
		(call)
	) else (
		echo Continuing...
		(call )
	)
) else (
	(call )
)
goto :eof

:run_patch
echo Attempting to patch "%sourcefile%"...
%app% -d -f -s "%sourcefile%" "%changes%" "%targetfile%"
if exist "%targetfile%" (
	mkdir %olddir% 2>nul
	move "%sourcefile%" %olddir%
	echo Done.
	(call )
	goto :eof
)
echo Error occured! Patching wasn't successful!
(call)
pause
goto :eof

:gtfo
chdir /d %WORKINGDIR%
(call )
goto :eof