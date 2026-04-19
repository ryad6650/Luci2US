$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut('C:\Users\louis\Desktop\Luci2US.lnk')
$s.TargetPath = 'C:\Users\louis\Luci2US\Luci2US.bat'
$s.WorkingDirectory = 'C:\Users\louis\Luci2US'
$s.IconLocation = 'C:\Users\louis\Luci2US\assets\icon.ico'
$s.WindowStyle = 7
$s.Description = 'Luci2US - Scan runes SW'
$s.Save()
Write-Host "Shortcut created:" $s.FullName
