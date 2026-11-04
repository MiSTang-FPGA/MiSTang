# Big always-on-top window with a sound and an OK button. Blocks until OK is pressed.
# usage: powershell -File tools/notify.ps1 -Title "Board action needed" -Text "Hold S1 and press OK"
param([string]$Title = 'MiSTang', [Parameter(Mandatory)][string]$Text)
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$f = New-Object Windows.Forms.Form
$f.Text = $Title; $f.TopMost = $true; $f.StartPosition = 'CenterScreen'
$f.Size = New-Object Drawing.Size(900, 520); $f.BackColor = [Drawing.Color]::FromArgb(20, 20, 20)
$f.FormBorderStyle = 'FixedDialog'; $f.ControlBox = $false
$t = New-Object Windows.Forms.Label
$t.Text = $Title; $t.ForeColor = [Drawing.Color]::White; $t.Font = New-Object Drawing.Font('Segoe UI', 30, [Drawing.FontStyle]::Bold)
$t.Dock = 'Top'; $t.Height = 90; $t.TextAlign = 'MiddleCenter'
$m = New-Object Windows.Forms.Label
$m.Text = $Text; $m.ForeColor = [Drawing.Color]::FromArgb(230, 230, 230); $m.Font = New-Object Drawing.Font('Segoe UI', 22)
$m.Dock = 'Fill'; $m.TextAlign = 'MiddleCenter'
$b = New-Object Windows.Forms.Button
$b.Text = 'OK'; $b.Font = New-Object Drawing.Font('Segoe UI', 26, [Drawing.FontStyle]::Bold); $b.Dock = 'Bottom'; $b.Height = 110
$b.BackColor = [Drawing.Color]::White; $b.ForeColor = [Drawing.Color]::Black; $b.FlatStyle = 'Flat'
$b.Add_Click({ $f.Close() })
$f.AcceptButton = $b
$f.Controls.Add($m); $f.Controls.Add($t); $f.Controls.Add($b)
$timer = New-Object Windows.Forms.Timer; $timer.Interval = 1500
$timer.Add_Tick({ [Media.SystemSounds]::Exclamation.Play() })
$f.Add_Shown({ $f.Activate(); [Media.SystemSounds]::Exclamation.Play(); $timer.Start() })
[void]$f.ShowDialog()
$timer.Stop()
