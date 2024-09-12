@echo off
cd /d "%~dp0"
setlocal enabledelayedexpansion

:: Set local variables
for %%I in (.) do set "dir_current=%%~fI"
set "dir_download=%dir_current%\slm"
set "dir_existing=%dir_current%\_internal"
set "dir_existing_upgrade=%dir_existing%\program_files"
set "dir_donwload_upgrade=%dir_download%\_internal"
set "handle=%~1"
set "link=https://raw.githubusercontent.com/babsonnexus/stream-link-manager-for-channels/main/executables/slm_windows.zip"
set "outfile=slm.zip"
set "executable=slm.exe"
set "executable_path=%dir_current%\%executable%"
set "batch=slm.bat"
set "batch_path='%dir_current%\%batch%'"
set "run_command=powershell -NoProfile -ExecutionPolicy Bypass -Command ^"Start-Process -WindowStyle hidden '%executable_path%'^""
set "scheduled_task=schtasks /create /tn "Stream Link Manager for Channels^" /tr ^"%batch_path%^" /sc onlogon /rl highest /f"
set "temp_batch=%dir_current%\temp.bat"

if [%1] neq [] goto handles

:: Check if the executable file exists
if exist "%executable%" (
    :: Run Executable
    call %run_command%
) else (
    :: Display error message and pause
    echo Stream Link Manager not installed. Please install using 'slm.bat install'.
    timeout /T -1
)

goto end

:download
:: Check if the process is running
echo Checking to see if Stream Link Manager for Channels is running...
tasklist /FI "IMAGENAME eq %executable%" 2>NUL | find /I "%executable%" >NUL

:: If the process is found, kill it
if "%ERRORLEVEL%"=="0" (
    echo %executable% is running. Attempting to kill it...
    echo taskkill /F /IM !executable! > "%temp_batch%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"%temp_batch%\"' -Verb RunAs"
    echo Killing, please wait...
    timeout /NOBREAK /T 5
    del /f "%temp_batch%"
    echo %executable% has been terminated.
) else (
    echo %executable% is not running.
)

:: Download and extract files
echo Downloading Stream Link Manager for Channels files...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%link%' -OutFile '%outfile%'"
timeout /NOBREAK /T 5

echo Extracting Stream Link Manager for Channels files...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath .\%outfile%"
timeout /NOBREAK /T 5

if "%handle%"=="upgrade" (
    if exist "%dir_existing_upgrade%" (
    	echo Moving user program files...
        move /Y "%dir_existing_upgrade%" "%dir_donwload_upgrade%"
        timeout /NOBREAK /T 5
    )
)

echo Cleaning up files...
del /q "%outfile%"
if exist "%executable%" (
    del /Q "%executable%"
)
if exist %dir_existing% (
    rd /S /Q "%dir_existing%"
)
timeout /NOBREAK /T 5

echo Moving files to final destination...
xcopy /E /Y /Q "%dir_download%\*" "%dir_current%"
if exist "%dir_download%" rd /S /Q "%dir_download%"
timeout /NOBREAK /T 5

goto %return_path%

:handles
:: Handle additional commands

:: Install
if "%handle%"=="install" (
    echo WARNING: Installing will overwrite any existing installation and user files.
    :install_prompt
    choice /C YN /M "Do you wish to continue"
    if errorlevel 2 (
        echo Installation canceled.
        goto end
    ) else if errorlevel 1 (
        echo Beginning installation...
        set "return_path=continue_install"
        goto download
        :continue_install
        echo Installation completed!
        goto end
    ) else (
        echo Invalid input. Please enter Y or N.
        goto prompt
    )
)

:: Upgrade
if "%handle%"=="upgrade" (
    echo Beginning upgrade...
    set "return_path=continue_upgrade"
    goto download
    :continue_upgrade
    echo Upgrade completed!
    goto end
) 

:: Startup
if "%handle%"=="startup" (
    echo Setting Stream Link Manager for Channels to run on startup...
    echo !scheduled_task! > "%temp_batch%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"%temp_batch%\"' -Verb RunAs"
    echo Creating task, please wait...
    timeout /NOBREAK /T 5
    del /f "%temp_batch%"
    echo Startup task complete. To start now, just run 'slm.bat' with no handles.
    goto end
)

:: Port
if "%handle%"=="port" (
    :port_input
    set /P "port_number=Please enter a port number between 1000 and 9999 (or enter the default 5000): "
    echo You entered: [!port_number!]
    
    rem Check if the input is a positive integer between 1000 and 9999
    for /F "delims=0123456789" %%A in ("!port_number!") do (
        echo Invalid port number. Please enter a positive integer between 1000 and 9999.
        goto port_input
    )
    if !port_number! lss 1000 (
        echo Invalid port number. Please enter a positive integer between 1000 and 9999.
        goto port_input
    )
    if !port_number! gtr 9999 (
        echo Invalid port number. Please enter a positive integer between 1000 and 9999.
        goto port_input
    )
    
    rem Create the variable
    echo Saving port number to environment variables...
    setx "SLM_PORT" "!port_number!"
    echo Stream Link Manager for Channels port set to [!port_number!].

    rem Add a new inbound rule to Windows Firewall
    echo Opening port in Windows firewall...
    echo netsh advfirewall firewall add rule name="Stream Link Manager for Channels" dir=in action=allow protocol=TCP localport=!port_number! > "%temp_batch%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"%temp_batch%\"' -Verb RunAs"
    echo Please wait...
    timeout /NOBREAK /T 5
    del /f "%temp_batch%"
    echo Port !port_number! has been opened in Windows Firewall.

    :: Check if the port is open
    echo Checking if port !port_number! is open...
    netstat -an | find ":!port_number!" >nul
    if %errorlevel% neq 0 (
        echo Port !port_number! is not open or the server is not listening.
    ) else (
        echo Port !port_number! is open and the server is listening.
    )

    echo Please completely exit out of this command prompt and restart Stream Link Manager for Channels in a new window for the port to take effect.
    
    goto end
)

:: Invalid handle
if "%handle%" neq "install" (
    if "%handle%" neq "upgrade" (
        echo Invalid command. Usage: 'slm.bat [install ^| upgrade ^| startup ^| port]'
    )
)

:end
:: Exit the script
endlocal
exit /b
