# cmdchild.ps1 -- why cmd.exe in an AppContainer cannot start programs:
# run the same programs through cmd.exe by bare name and by full path.
# Creates one directory under %TEMP% and one AppContainer profile, and
# removes both at the end.
param([string[]]$Tests)
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:TEMP ('battery-cmd-' + (Get-Random))
$bin = "$root\bin"
New-Item -ItemType Directory $root, "$root\work", $bin | Out-Null
$source = Get-Content -Raw "$PSScriptRoot\sbx.cs"
Add-Type -TypeDefinition $source -OutputType ConsoleApplication `
         -OutputAssembly "$bin\sbx.exe"
function Grant($path, $sid, $rights) {
    $acl = Get-Acl $path
    $who = New-Object Security.Principal.SecurityIdentifier $sid
    $acl.AddAccessRule((New-Object `
        Security.AccessControl.FileSystemAccessRule($who, $rights,
        'ContainerInherit, ObjectInherit', 'None', 'Allow')))
    Set-Acl $path $acl
}
$profile = 'battery.cmdtest'
$sid = & "$bin\sbx.exe" mkprofile $profile
Grant $bin $sid ReadAndExecute
Grant "$root\work" $sid Modify
$sys = "$env:SystemRoot\System32"
$tests = if ($Tests) { $Tests } else { 'whoami', "$sys\whoami.exe", 'where whoami',
         'curl --version', "$sys\curl.exe --version", 'echo %PATH%',
         'dir /b C:\Windows\System32\whoami.exe' }
Push-Location "$root\work"
$ErrorActionPreference = 'Continue'        # cmd.exe's errors go to stderr
try {
    foreach ($t in $tests) {
        "== cmd /c $t"
        & "$bin\sbx.exe" appcontainer --sid $sid -- `
            "$sys\cmd.exe" /c $t 2>&1 | Select-Object -First 2 |
            ForEach-Object { "   $_" }
        "   exit $LASTEXITCODE"
    }
} finally {
    Pop-Location
    & "$bin\sbx.exe" rmprofile $profile | Out-Null
    Remove-Item -Recurse -Force $root
}
