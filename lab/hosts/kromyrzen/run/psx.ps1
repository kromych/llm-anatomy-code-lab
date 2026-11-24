# psx.ps1 -- run the lines of a file one by one as at a PowerShell prompt:
# print "PS> line" (and ">> line" for a continuation), then run it in
# this session.  A line that begins with "#" is printed as it is.
#   powershell -ExecutionPolicy Bypass -File psx.ps1 COMMANDS.txt [DIR]
param([string]$File, [string]$Dir = '')
if ($Dir) { Set-Location $Dir }
if ($PSStyle) { $PSStyle.OutputRendering = 'PlainText' }  # no colors
$psxLines = @(Get-Content $File)
$psxI = 0
while ($psxI -lt $psxLines.Count) {
    $psxCmd = $psxLines[$psxI]
    $psxI++
    if ($psxCmd -match '^\s*$') { [Console]::Out.WriteLine(''); continue }
    if ($psxCmd -match '^#') { [Console]::Out.WriteLine($psxCmd); continue }
    [Console]::Out.WriteLine("PS> $psxCmd")
    while ($psxCmd -match '[`|{]\s*$' -and $psxI -lt $psxLines.Count) {
        [Console]::Out.WriteLine(">> " + $psxLines[$psxI])
        $psxCmd += "`n" + $psxLines[$psxI]
        $psxI++
    }
    [Console]::Out.Flush()
    try { $psxBlock = [scriptblock]::Create($psxCmd) }
    catch {                                 # a parse error, as at a prompt
        [Console]::Out.WriteLine($_.Exception.InnerException.Message)
        continue
    }
    try { . $psxBlock | Out-Default }
    catch { $_ | Out-Default }
}
