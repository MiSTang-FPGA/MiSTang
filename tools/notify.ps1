# Big always-on-top window with a sound and an OK button. Blocks until OK is pressed.
# With -Buttons 'Yes','No' the process exit code is the index of the pressed button (0, 1, ...).
# usage: powershell -File tools/notify.ps1 -Title "Board action needed" -Text "Hold S1 and press OK"
param([string]$Title = 'MiSTang', [Parameter(Mandatory)][string]$Text, [string[]]$Buttons = @('OK'))
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$f = New-Object Windows.Forms.Form
$f.Text = $Title; $f.TopMost = $true; $f.StartPosition = 'CenterScreen'
$f.Size = New-Object Drawing.Size(900, (420 + 110 * $Buttons.Count)); $f.BackColor = [Drawing.Color]::FromArgb(20, 20, 20)
$f.FormBorderStyle = 'FixedDialog'; $f.ControlBox = $false
$t = New-Object Windows.Forms.Label
$t.Text = $Title; $t.ForeColor = [Drawing.Color]::White; $t.Font = New-Object Drawing.Font('Segoe UI', 30, [Drawing.FontStyle]::Bold)
$t.Dock = 'Top'; $t.Height = 90; $t.TextAlign = 'MiddleCenter'
$m = New-Object Windows.Forms.Label
$m.Text = $Text; $m.ForeColor = [Drawing.Color]::FromArgb(230, 230, 230); $m.Font = New-Object Drawing.Font('Segoe UI', 22)
$m.Dock = 'Fill'; $m.TextAlign = 'MiddleCenter'
$script:answer = 0
$panel = New-Object Windows.Forms.FlowLayoutPanel
$panel.Dock = 'Bottom'; $panel.Height = 110 * $Buttons.Count + 10; $panel.FlowDirection = 'TopDown'; $panel.WrapContents = $false
$panel.Padding = New-Object Windows.Forms.Padding(20, 5, 0, 5)
for ($i = 0; $i -lt $Buttons.Count; $i++) {
    $b = New-Object Windows.Forms.Button
    $b.Text = $Buttons[$i]; $b.Font = New-Object Drawing.Font('Segoe UI', 24, [Drawing.FontStyle]::Bold)
    $b.Width = 840; $b.Height = 100
    $b.BackColor = [Drawing.Color]::White; $b.ForeColor = [Drawing.Color]::Black; $b.FlatStyle = 'Flat'
    $b.Tag = $i
    $b.Add_Click({ param($s, $e) $script:answer = [int]$s.Tag; $f.Close() })
    $panel.Controls.Add($b)
}
$f.Controls.Add($m); $f.Controls.Add($t); $f.Controls.Add($panel)
$timer = New-Object Windows.Forms.Timer; $timer.Interval = 1500
$timer.Add_Tick({ [Media.SystemSounds]::Exclamation.Play() })
$f.Add_Shown({ $f.Activate(); [Media.SystemSounds]::Exclamation.Play(); $timer.Start() })
[void]$f.ShowDialog()
$timer.Stop()
exit $script:answer

