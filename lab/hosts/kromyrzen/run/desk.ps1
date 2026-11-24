# desk.ps1 -- two runs of run-windows.ps1 in one logon, with the entries
# on the window station and the desktop listed before, between and after,
# and the entries that the runs added removed at the end (Chapter 16).
#   powershell -NoProfile -ExecutionPolicy Bypass -File desk.ps1 [-Out DIR]
param([string]$Out = (Join-Path $PSScriptRoot 'desk-out'),
      [int]$Runs = 2)
$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory $Out -Force | Out-Null
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Ws
{
    [StructLayout(LayoutKind.Sequential)]
    struct ExplicitAccess                       // EXPLICIT_ACCESS + TRUSTEE
    {
        public uint rights;
        public int mode, inheritance;
        public IntPtr multiple;
        public int operation, form, type;
        public IntPtr sid;
    }
    const string A = "advapi32", W = "user32";
    [DllImport("kernel32")] static extern int GetCurrentThreadId();
    [DllImport(W)] static extern IntPtr GetProcessWindowStation();
    [DllImport(W)] static extern IntPtr GetThreadDesktop(int thread);
    [DllImport(W, CharSet = CharSet.Unicode)]
    static extern bool GetUserObjectInformation(IntPtr h, int index,
        StringBuilder name, int size, out int needed);
    [DllImport(W, CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr OpenWindowStation(string name, bool inherit,
        uint access);
    [DllImport(W, CharSet = CharSet.Unicode, SetLastError = true)]
    static extern IntPtr OpenDesktop(string name, int flags, bool inherit,
        uint access);
    [DllImport(A)]
    static extern int GetSecurityInfo(IntPtr h, int type, int info,
        IntPtr owner, IntPtr group, out IntPtr dacl, IntPtr sacl,
        out IntPtr descriptor);
    [DllImport(A, CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool ConvertSecurityDescriptorToStringSecurityDescriptor(
        IntPtr descriptor, int revision, int info, out IntPtr text,
        out int length);
    [DllImport(A, CharSet = CharSet.Unicode, SetLastError = true)]
    static extern bool ConvertStringSidToSid(string s, out IntPtr sid);
    [DllImport(A)]
    static extern int SetEntriesInAcl(int count, ref ExplicitAccess entry,
        IntPtr old, out IntPtr result);
    [DllImport(A)]
    static extern int SetSecurityInfo(IntPtr h, int type, int info,
        IntPtr owner, IntPtr group, IntPtr dacl, IntPtr sacl);

    static IntPtr Open(bool desktop, uint access, out string name)
    {
        IntPtr current = desktop ? GetThreadDesktop(GetCurrentThreadId())
                                 : GetProcessWindowStation();
        var s = new StringBuilder(256);
        int needed;
        GetUserObjectInformation(current, 2, s, 512, out needed);
        name = s.ToString();
        return desktop ? OpenDesktop(name, 0, false, access)
                       : OpenWindowStation(name, false, access);
    }

    public static string Name(bool desktop)
    {
        string name;
        Open(desktop, 0x20000, out name);
        return name;
    }

    // The DACL of the window station or the desktop, in SDDL.
    public static string Sddl(bool desktop)
    {
        string name;
        IntPtr h = Open(desktop, 0x20000, out name);    // READ_CONTROL
        if (h == IntPtr.Zero)
            return "cannot open " + name + ": error " +
                   Marshal.GetLastWin32Error();
        IntPtr dacl, descriptor, text;
        int length;
        int r = GetSecurityInfo(h, 7, 4, IntPtr.Zero, IntPtr.Zero,
                                out dacl, IntPtr.Zero, out descriptor);
        if (r != 0) return "GetSecurityInfo: error " + r;
        ConvertSecurityDescriptorToStringSecurityDescriptor(descriptor, 1,
            4, out text, out length);
        return Marshal.PtrToStringUni(text);
    }

    // Remove the entries of sid (SetEntriesInAcl with REVOKE_ACCESS).
    public static int Revoke(bool desktop, string sidText)
    {
        string name;
        IntPtr h = Open(desktop, 0x60000, out name);    // and WRITE_DAC
        if (h == IntPtr.Zero) return Marshal.GetLastWin32Error();
        IntPtr sid, dacl, descriptor, result;
        if (!ConvertStringSidToSid(sidText, out sid))
            return Marshal.GetLastWin32Error();
        int r = GetSecurityInfo(h, 7, 4, IntPtr.Zero, IntPtr.Zero,
                                out dacl, IntPtr.Zero, out descriptor);
        if (r != 0) return r;
        var entry = new ExplicitAccess { mode = 4, sid = sid };
        r = SetEntriesInAcl(1, ref entry, dacl, out result);
        if (r != 0) return r;
        return SetSecurityInfo(h, 7, 4, IntPtr.Zero, IntPtr.Zero, result,
                               IntPtr.Zero);
    }
}
'@
$source = Get-Content -Raw "$PSScriptRoot\sbx.cs"
Add-Type -TypeDefinition $source -OutputType ConsoleApplication `
         -OutputAssembly "$Out\sbx.exe"

function Sids($desktop) {               # the SIDs of the entries
    [regex]::Matches([Ws]::Sddl($desktop), '\(([^)]*)\)') |
        ForEach-Object { ($_.Groups[1].Value -split ';')[5] }
}
function Say($text) { Add-Content "$Out\checks.txt" $text }
function State($label) {
    $w = @(Sids $false); $d = @(Sids $true)
    Add-Content "$Out\full.txt" "## $label"
    Add-Content "$Out\full.txt" ("window station " + [Ws]::Sddl($false))
    Add-Content "$Out\full.txt" ("desktop        " + [Ws]::Sddl($true))
    $aw = @($w | Where-Object { $script:w0 -notcontains $_ })
    $ad = @($d | Where-Object { $script:d0 -notcontains $_ })
    Say ("{0}: {1} entries on the window station, {2} on the desktop" -f
         $label, $w.Count, $d.Count)
    if ($script:w0) {
        Say ("   not there at the start, window station: " +
             $(if ($aw) { $aw -join ' ' } else { 'none' }))
        Say ("   not there at the start, desktop: " +
             $(if ($ad) { $ad -join ' ' } else { 'none' }))
    }
    return ,@($aw + $ad | Select-Object -Unique)
}
function LowIl($label) {                # does user32 load at low integrity
    $text = & "$Out\sbx.exe" lowil -- whoami 2>&1 | Out-String
    $text = $text.Trim() -replace '\\[^\\]+$', '\<user>'
    Say ("{0}: sbx lowil -- whoami: exit code {1} (0x{1:X8}) {2}" -f
         $label, $LASTEXITCODE, $text)
}

Remove-Item "$Out\checks.txt", "$Out\full.txt", "$Out\done.txt" `
    -ErrorAction SilentlyContinue
$me = Get-Process -Id $PID
$level = (whoami /groups | Select-String 'Mandatory Label') -replace
         '\s+', ' '
Say ("session {0}, window station {1}, desktop {2}, {3}" -f
     $me.SessionId, [Ws]::Name($false), [Ws]::Name($true),
     ($level -replace '^.*\\(\S+ Mandatory Level).*$', '$1'))
Say ("PowerShell {0}, Windows {1}" -f $PSVersionTable.PSVersion,
     (Get-CimInstance Win32_OperatingSystem).Version)
$w0 = $null; $d0 = $null
State 'before the first run' | Out-Null
$w0 = @(Sids $false); $d0 = @(Sids $true)
LowIl 'before the first run'
foreach ($n in 1..$Runs) {
    powershell -ExecutionPolicy Bypass -File `
        "$PSScriptRoot\run-windows.ps1" > "$Out\run$n.txt" 2>&1
    $added = State "after run $n"
    LowIl "after run $n"
}
foreach ($sid in $added) {              # leave the logon as it was
    $r = [Ws]::Revoke($false, $sid), [Ws]::Revoke($true, $sid)
    Say ("removed the entries of {0}: results {1} and {2}" -f $sid,
         $r[0], $r[1])
}
$left = State 'after the removal'
LowIl 'after the removal'
Say ("the lists are as at the start: " +
     ((((Sids $false) -join ' ') -eq ($w0 -join ' ')) -and
      (((Sids $true) -join ' ') -eq ($d0 -join ' '))))
Set-Content "$Out\done.txt" 'done'
