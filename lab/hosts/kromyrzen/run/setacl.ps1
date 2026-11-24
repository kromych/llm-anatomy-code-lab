# setacl.ps1 -- why a label set on work does not reach .git once the
# Grant of run-windows.ps1 (Get-Acl, Set-Acl) has touched .git
# (Chapter 16).  Makes two directories next to itself and removes them.
#   powershell -ExecutionPolicy Bypass -File setacl.ps1
Set-Location $PSScriptRoot
function Grant($path, $sid, $rights, $type = 'Allow') {  # the runner's
    $acl = Get-Acl $path
    $who = New-Object Security.Principal.SecurityIdentifier $sid
    $acl.AddAccessRule((New-Object `
        Security.AccessControl.FileSystemAccessRule($who, $rights,
        'ContainerInherit, ObjectInherit', 'None', $type)))
    Set-Acl $path $acl
}
function Show($root) {
    foreach ($p in '', '\.git', '\.git\hooks') {
        $line = (icacls "$root$p" | Select-String 'Mandatory Label')
        $line = $line -replace '^\s+', ''
        $sacl = (Get-Acl "$root$p" -Audit).AreAuditRulesProtected
        '{0,-16} SACL protected: {1,-5} {2}' -f "work$p", $sacl,
            $(if ($line) { $line } else { '(no label)' })
    }
}
foreach ($case in 'no Set-Acl', 'Set-Acl on .git') {
    $w = 'f-' + ($case -replace '\W', '') + '\work'
    New-Item -ItemType Directory "$w\.git\hooks" | Out-Null
    "== $case, before the label"
    if ($case -like 'Set-Acl*') {
        Grant "$w\.git" 'S-1-5-21-1-2-3-4' 'Write' Deny
    }
    Show $w
    "== $case, after icacls work /setintegritylevel (OI)(CI)Low"
    icacls $w /setintegritylevel '(OI)(CI)Low' | Out-Null
    Show $w
}
Remove-Item -Recurse -Force f-noSetAcl, f-SetAclongit
