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
# Turns the FPS choice on in metin2client.exe (MT2009 PLUS 2.0.56 / 2.0.57 / 2.0.60 / 2.0.62 / 2.0.63 - 2.0.62 ma ten sam exe co 2.0.60), or back
# off. With it on, the rate (60 / 120 / 144 / 240) is picked in game:
# Opcje Gry > System > FPS. Same bytes as tools/patch_fps.py, which explains them.
try {
	$exe = Join-Path (Split-Path -Parent $env:M2_SELF) 'metin2client.exe'
	if (-not (Test-Path $exe)) { throw "Nie ma $exe - wrzuc ten plik do folderu klienta." }
	if (Get-Process metin2client -ErrorAction SilentlyContinue) { throw 'Najpierw zamknij gre (metin2client).' }

	# (file offset, original bytes, patched bytes) per client exe; 'cam' is the
	# camera byte (app.SetCameraSpeed leaves the mouse sensitivity alone, so root's
	# updateable.py can slow the camera keys down to the 60 FPS speed) - it came
	# later: an exe patched by the older .bat has every block but that one.
	$versions = [ordered]@{
		'2.0.63' = @{ cam = 0x284eee; blocks = @(
		@(0x26c6e0, '8b44240489817c7e0200c20400', 'e97bdd60009090909090909090'),
		@(0x2dc719, '8b4e1841894e1883f901750ac74618ffffffff83c9ff8b460c83e10183c01003c8', 'e9e0154f0090909090909090909090909090909090909090909090909090909090'),
		@(0x2dc894, '75', 'eb'),
		@(0x284eee, '74', 'eb'),
		@(0x7cdcfe, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b46188bc8c1e91083f91e720881f9f40100007607b93c00000033c025ffff000005e803000033d251f7f159c1e1100bd189561889461403460c8bc8e9fbe9b0ff'),
		@(0x87a460, 'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccc', '8b442404c1e010e800000000598b898c523c0085c97403894118c20400')
		) }
		'2.0.60 / 2.0.62' = @{ cam = 0x284e6e; blocks = @(
		@(0x290, '74ab9500', '00ac9500'),
		@(0x26c660, '8b44240489817c7e0200c20400', 'e96be96e009090909090909090'),
		@(0x2dc6b9, '8b4e1841894e1883f901750ac74618ffffffff83c9ff8b460c83e10183c01003c8', 'e9c2e8670090909090909090909090909090909090909090909090909090909090'),
		@(0x2dc834, '75', 'eb'),
		@(0x284e6e, '74', 'eb'),
		@(0x95af80, '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', '8b46188bc8c1e91083f91e720881f9f40100007607b93c00000033c025ffff000005e803000033d251f7f159c1e1100bd189561889461403460c8bc8e9191798ff0000000000000000000000000000008b442404c1e010e800000000598b89d4462e0085c97403894118c2040000000000000000000000000000000000000000')
		) }
		'2.0.57' = @{ cam = 0x28409e; blocks = @(
		@(0x298, '649b9500', '009c9500'),
		@(0x26b880, '8b44240489814c7e0200c20400', 'e93be76e009090909090909090'),
		@(0x2db7d9, '8b4e1841894e1883f901750ac74618ffffffff83c9ff8b460c83e10183c01003c8', 'e992e7670090909090909090909090909090909090909090909090909090909090'),
		@(0x2db954, '75', 'eb'),
		@(0x28409e, '74', 'eb'),
		@(0x959f70, '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', '8b46188bc8c1e91083f91e720881f9f40100007607b93c00000033c025ffff000005e803000033d251f7f159c1e1100bd189561889461403460c8bc8e9491898ff0000000000000000000000000000008b442404c1e010e800000000598b892c352e0085c97403894118c2040000000000000000000000000000000000000000')
		) }
		'2.0.56' = @{ cam = 0x27fcbe; blocks = @(
		@(0x290, '544e9500', '00509500'),
		@(0x2674c0, '8b442404898134770200c20400', 'e9ebdd6e009090909090909090'),
		@(0x2d7519, '8b4e1841894e1883f901750ac74618ffffffff83c9ff8b460c83e10183c01003c8', 'e942dd670090909090909090909090909090909090909090909090909090909090'),
		@(0x2d7694, '75', 'eb'),
		@(0x27fcbe, '74', 'eb'),
		@(0x955260, '0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', '8b46188bc8c1e91083f91e720881f9f40100007607b93c00000033c025ffff000005e803000033d251f7f159c1e1100bd189561889461403460c8bc8e9992298ff0000000000000000000000000000008b442404c1e010e800000000598b89c42f2e0085c97403894118c2040000000000000000000000000000000000000000')
		) }
	}
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
	foreach ($ver in $versions.Keys) {
		$blocks = $versions[$ver].blocks; $cam = $versions[$ver].cam
		if (Matches $data 1) { $now = 'wylaczony' }
		elseif (Matches $data 2) { $now = 'wlaczony' }
		elseif ((Matches $data 2 $cam) -and $data[$cam] -eq 0x74) { $now = 'wlaczony (stara wersja, bez poprawki kamery - wybierz 1 jeszcze raz)' }
		elseif ((Matches $data 1 $cam) -and $data[$cam] -eq 0xeb) { $now = 'wylaczony' }  # cofniety starym .bat
		if ($now) { break }
	}
	if (-not $now) { throw 'To nie jest metin2client.exe z klienta 2.0.56, 2.0.57, 2.0.60, 2.0.62 ani 2.0.63 (inne bajty).' }
	Write-Host "Klient $ver"
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
