@echo off
setlocal
title MT2009 Plus - wybor modow
rem Instalator z wyborem modow. Kod jest w instalator\Instalator.cs: PowerShell kompiluje go
rem w pamieci (Add-Type, kompilator C# z .NET Framework) i uruchamia - bez zapisywania
rem zadnego pliku .exe (taki plik Windows potrafi zablokowac: "This app can't run on your PC").
set "M2_PKG=%~dp0"
set "M2_CS=%~dp0instalator\Instalator.cs"
if not exist "%M2_CS%" (
	echo Brak instalator\Instalator.cs - uruchom ten plik z rozpakowanej paczki MT2009_Gotowe.
	set "M2_RC=1"
	goto koniec
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "try { Add-Type -TypeDefinition ([IO.File]::ReadAllText($env:M2_CS)) -Language CSharp -ErrorAction Stop } catch { Write-Host ('Nie udalo sie skompilowac instalatora: ' + $_.Exception.Message) -ForegroundColor Red; exit 2 }; exit ([MT2009.Instalator]::Main(@()))"
set "M2_RC=%ERRORLEVEL%"

:koniec
echo.
if not "%M2_RC%"=="0" echo Instalacja nie zostala dokonczona (kod %M2_RC%).
pause
exit /b %M2_RC%
