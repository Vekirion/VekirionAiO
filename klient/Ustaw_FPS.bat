@echo off
setlocal
title MT2009 Plus - limit FPS
set "M2_SELF=%~f0"
set "M2_ARG=%~1"

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:M2_SELF); $m='# POWERSHELL START'; $i=$s.LastIndexOf($m); Invoke-Expression $s.Substring($i+$m.Length)"
set "M2_RESULT=%ERRORLEVEL%"

echo.
if not "%M2_RESULT%"=="0" echo Nic nie zostalo zmienione.
if "%M2_ARG%"=="" pause
exit /b %M2_RESULT%

# POWERSHELL START
$ErrorActionPreference = 'Stop'
# Turns the FPS choice on in metin2client.exe, or back off. With it on, the rate
# (60 / 120 / 144 / 240) is picked in game: Opcje Gry > System > FPS.
# Works only for the client version this package is made for ($supported): the version
# is read from CLIENT_VERSION in the client folder. Older versions are out of date
# (update the client with MT2009-Patcher.exe), newer ones need a newer package.
try {
	$supported = '2.0.68'

	$dir = Split-Path -Parent $env:M2_SELF
	$exe = Join-Path $dir 'metin2client.exe'
	$verFile = Join-Path $dir 'CLIENT_VERSION'
	if (-not (Test-Path $exe)) { throw "Nie ma $exe - wrzuc ten plik do folderu klienta." }
	if (-not (Test-Path $verFile)) { throw "Nie ma pliku CLIENT_VERSION w $dir - nie wiem, jaka to wersja klienta. Uruchom MT2009-Patcher.exe." }

	$ver = ([IO.File]::ReadAllText($verFile)).Trim()
	$v = $null
	if (-not [Version]::TryParse($ver, [ref]$v)) { throw "Nieczytelna wersja w CLIENT_VERSION: '$ver'." }
	$sv = [Version]$supported
	Write-Host "Klient $ver (CLIENT_VERSION)"
	if ($v -lt $sv) {
		throw "Wersja $ver jest NIEAKTUALNA i nie jest obslugiwana. Ten plik obsluguje tylko klienta $supported - zaktualizuj klienta programem MT2009-Patcher.exe."
	}
	if ($v -gt $sv) {
		throw "Wersja $ver jest nowsza niz $supported, dla ktorej jest ten plik - pobierz nowsza paczke Vekirion AiO."
	}
	if (Get-Process metin2client -ErrorAction SilentlyContinue) { throw 'Najpierw zamknij gre (metin2client).' }

	# (file offset, original bytes, patched bytes) of the 2.0.68 exe (the same exe as in
	# 2.0.63-2.0.67); 'cam' is the camera byte (app.SetCameraSpeed leaves the mouse
	# sensitivity alone, so root's updateable.py can slow the camera keys down to the
	# 60 FPS speed) - an exe patched by a very old .bat has every block but that one.
	$cam = 0x284eee
	$blocks = @(
		@(0x26c6e0, '8b44240489817c7e0200c20400', 'e97bdd60009090909090909090'),
		@(0x2dc719, '8b4e1841894e1883f901750ac74618ffffffff83c9ff8b460c83e10183c01003c8', 'e9e0154f0090909090909090909090909090909090909090909090909090909090'),
		@(0x2dc894, '75', 'eb'),
		@(0x284eee, '74', 'eb'),
		@(0x7cdcfe, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b46188bc8c1e91083f91e720881f9f40100007607b93c00000033c025ffff000005e803000033d251f7f159c1e1100bd189561889461403460c8bc8e9fbe9b0ff'),
		@(0x87a460, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b442404c1e010e800000000598b898c523c0085c97403894118c20400')
	)
	function Hex($h) { $b = New-Object byte[] ($h.Length / 2); for ($i = 0; $i -lt $b.Length; $i++) { $b[$i] = [Convert]::ToByte($h.Substring(2 * $i, 2), 16) }; ,$b }
	function Matches($data, $col, $skip = -1) {
		foreach ($blk in $blocks) {
			if ($blk[0] -eq $skip) { continue }
			$want = Hex $blk[$col]
			if ($blk[0] + $want.Length -gt $data.Length) { return $false }
			for ($i = 0; $i -lt $want.Length; $i++) { if ($data[$blk[0] + $i] -ne $want[$i]) { return $false } }
		}
		return $true
	}

	$data = [IO.File]::ReadAllBytes($exe)
	$now = $null
	if (Matches $data 1) { $now = 'wylaczony' }
	elseif (Matches $data 2) { $now = 'wlaczony' }
	elseif ((Matches $data 2 $cam) -and $data[$cam] -eq 0x74) { $now = 'wlaczony (stara wersja, bez poprawki kamery - wybierz 1 jeszcze raz)' }
	elseif ((Matches $data 1 $cam) -and $data[$cam] -eq 0xeb) { $now = 'wylaczony' }
	if (-not $now) { throw "metin2client.exe nie pasuje do klienta $supported (inne bajty). Uruchom MT2009-Patcher.exe, zeby przywrocic oryginalny exe." }
	Write-Host "Wybor FPS w grze: teraz $now"

	$choice = $env:M2_ARG
	if (-not $choice) {
		Write-Host ''
		Write-Host '  1 = wlacz (FPS wybierasz w grze: Opcje Gry > System > FPS)'
		Write-Host '  0 = wylacz (oryginalny exe, ~60 FPS)'
		$choice = Read-Host 'Wybierz'
	}
	switch ($choice.Trim()) {
		{ $_ -in '1', 'on' } { $col = 2 }
		{ $_ -in '0', 'off' } { $col = 1 }
		default { throw "Nieznany wybor: $choice" }
	}

	foreach ($blk in $blocks) {
		$b = Hex $blk[$col]
		[Array]::Copy($b, 0, $data, $blk[0], $b.Length)
	}
	[IO.File]::WriteAllBytes($exe, $data)
	if ($col -eq 2) { Write-Host 'Gotowe: wlaczony. Uruchom gre i wybierz FPS w Opcje Gry > System.' }
	else { Write-Host 'Gotowe: oryginalny exe (~60 FPS).' }
	exit 0
} catch {
	Write-Host $_.Exception.Message
	exit 1
}
