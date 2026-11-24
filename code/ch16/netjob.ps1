# netjob.ps1 -- compile netjob.cs and run it without a job and under rate
# limits of 1 and 1000 bytes per second.  Leaves nothing behind.
$dir = Join-Path $env:TEMP ('battery-net-' + (Get-Random))
New-Item -ItemType Directory $dir | Out-Null
try {
    Add-Type -TypeDefinition (Get-Content -Raw "$PSScriptRoot\netjob.cs") `
             -OutputType ConsoleApplication -OutputAssembly "$dir\netjob.exe"
    foreach ($rate in 0, 1, 1000) {
        "== rate $rate bytes/s" + $(if ($rate -eq 0) { ' (no job)' })
        & "$dir\netjob.exe" $rate 1000000
    }
} finally { Remove-Item -Recurse -Force $dir }
