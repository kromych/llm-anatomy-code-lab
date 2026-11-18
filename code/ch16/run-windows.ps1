# Run the battery under each Windows mechanism (Chapter 16).  The run
# creates one directory under -Base (%TEMP% unless given) and one
# AppContainer profile, and removes both at the end.  The mechanisms
# codex and codex+elevated are the two backends of Codex CLI's own
# sandbox, and srt is Anthropic's sandbox runtime; the last two need
# the setup of their tool first.  Give all three a -Base outside
# %TEMP%, where they allow writes.
# With -Times n, time n starts of cmd /c exit 0 under each instead.
param([string]$Mechanisms = ('none,none+job,none+tree,restricted,' +
          'lowil,appcontainer,appcontainer+job'),
      [int]$Times = 0, [string]$Base = $env:TEMP)
$ErrorActionPreference = 'Stop'
$root = Join-Path $Base ('battery-sbx-' + (Get-Random))
$bin = "$root\bin"
$git = "$root\work\.git"                   # stays closed to the sandbox
$dirs = $root, "$root\work", "$root\outside", "$root\secret", $bin,
        $git, "$git\hooks"
New-Item -ItemType Directory $dirs | Out-Null
Set-Content "$root\secret\token.txt" 'dummy-token-not-a-real-secret'
foreach ($name in 'battery', 'sbx') {
    $source = Get-Content -Raw "$PSScriptRoot\$name.cs"
    Add-Type -TypeDefinition $source -OutputType ConsoleApplication `
             -OutputAssembly "$bin\$name.exe"
}
$listener = Start-Process "$bin\battery.exe" -NoNewWindow -PassThru `
    -ArgumentList 'listen', "$root\port", "$root\log"
while (-not (Test-Path "$root\port")) { Start-Sleep -Milliseconds 100 }
Start-Sleep -Milliseconds 200
$port = Get-Content "$root\port"
$battery = "$bin\battery.exe", $root, $port
$profile = 'battery.sandbox'
$codexHome = $env:CODEX_HOME               # as the user has it

function Grant($path, $sid, $rights, $type = 'Allow') {
    $acl = Get-Acl $path                   # icacls cannot name any SID
    $who = New-Object Security.Principal.SecurityIdentifier $sid
    $acl.AddAccessRule((New-Object `
        Security.AccessControl.FileSystemAccessRule($who, $rights,
        'ContainerInherit, ObjectInherit', 'None', $type)))
    Set-Acl $path $acl
}
$nowrite = 'Write, Delete, DeleteSubdirectoriesAndFiles'

function Launch($command) {                # run it under $exe @opts
    if ($exe -eq 'srt.cmd') { & $exe @opts -c "$command" }
    else { & $exe @opts -- @command }      # srt takes one string, and
}                                          # quotes arguments for sh

Push-Location "$root\work"                 # the sandbox's current dir
try {
    foreach ($mech in $Mechanisms -split ',') {
        Remove-Item "$root\work\ok.txt", "$root\outside\probe.txt",
                    "$git\hooks\pre-commit", "$root\work\orphan.txt",
                    "$root\log" -ErrorAction SilentlyContinue
        "== $mech"
        $exe = "$bin\sbx.exe"
        $opts = @($mech -replace '\+(job|tree)$')
        if ($mech -like '*+job') { $opts += '--job' }
        if ($mech -like '*+tree') { $opts += '--tree' }
        if ($mech -like 'codex*') {         # Codex CLI's own sandbox
            $kind = 'elevated'              # its accounts' passwords are
            $env:CODEX_HOME = $codexHome    # in the user's CODEX_HOME
            if ($mech -eq 'codex') {        # the restricted token alone
                $kind = 'unelevated'
                $env:CODEX_HOME = "$root\codex-home"
                New-Item -ItemType Directory $env:CODEX_HOME -Force |
                    Out-Null
            }
            $exe = 'codex'
            $opts = '-c', "windows.sandbox=$kind", 'sandbox', '-P',
                    ':workspace', '-C', "$root\work"
        }
        if ($mech -eq 'srt') {              # Anthropic's sandbox runtime
            @{ network = @{ allowedDomains = @(); deniedDomains = @() }
               filesystem = @{ denyRead = @("$root\secret")
                               allowRead = @($bin)
                               allowWrite = @("$root\work")
                               denyWrite = @() } } |
                ConvertTo-Json -Depth 3 | Set-Content "$root\srt.json"
            $exe = 'srt.cmd'
            $opts = '--settings', "$root\srt.json"
        }
        if ($mech -eq 'restricted') {       # a random capability SID
            $r = 1..4 | ForEach-Object { Get-Random -Maximum 2000000000 }
            $sid = 'S-1-5-21-' + ($r -join '-')
            Grant "$root\work" $sid Modify
            Grant $git $sid $nowrite Deny
            $opts += '--sid', $sid
        }
        if ($mech -eq 'lowil') {
            icacls "$root\work" /setintegritylevel '(OI)(CI)Low' |
                Out-Null
            icacls $git /setintegritylevel '(OI)(CI)Medium' | Out-Null
        }
        if ($mech -like 'appcontainer*') {
            $sid = & "$bin\sbx.exe" mkprofile $profile
            Grant $bin $sid ReadAndExecute
            Grant "$root\work" $sid Modify
            Grant $git $sid $nowrite Deny
            $opts += '--sid', $sid
        }
        if ($Times -gt 0) {
            $ms = 1..$Times | ForEach-Object {
                (Measure-Command {
                    Launch $env:ComSpec, '/c', 'exit', '0'
                }).TotalMilliseconds } | Sort-Object
            '   median of {0} starts: {1:f1} ms' -f $Times,
                $ms[[int][math]::Floor($Times / 2)]
            continue
        }
        Launch $battery
        Start-Sleep -Seconds 3              # time for an orphan's mark
        $ok, $w, $h, $o = "$root\work\ok.txt", "$root\outside\probe.txt",
            "$git\hooks\pre-commit", "$root\work\orphan.txt" |
            ForEach-Object { if (Test-Path $_) { 'yes' } else { 'no' } }
        $n = if (Test-Path "$root\log") { @(Get-Content "$root\log").Count }
             else { 0 }
        "   on the host: ok.txt $ok, probe.txt $w, pre-commit $h, " +
            "orphan.txt $o, connections $n"
    }
} finally {
    Pop-Location
    & "$bin\sbx.exe" rmprofile $profile | Out-Null
    Stop-Process $listener
    Start-Sleep -Milliseconds 300
    Remove-Item -Recurse -Force $root
}
