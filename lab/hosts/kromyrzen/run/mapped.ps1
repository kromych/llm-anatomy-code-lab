# mapped.ps1 -- list what a process has mapped as data (regions of type
# MEM_MAPPED) with the bytes of each: the name of the file, or
# "(no name)" for a section without one, as GetMappedFileName reports.
#   powershell -ExecutionPolicy Bypass -File mapped.ps1 PID [PATTERN]
param([int]$Id, [string]$Pattern = '.')
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class Mapped
{
    [StructLayout(LayoutKind.Sequential)]
    struct Mbi
    {
        public IntPtr baseAddress, allocationBase;
        public uint allocationProtect, pad1;
        public IntPtr regionSize;
        public uint state, protect, type, pad2;
    }
    [DllImport("kernel32", SetLastError = true)]
    static extern IntPtr OpenProcess(uint access, bool inherit, int pid);
    [DllImport("kernel32")]
    static extern IntPtr VirtualQueryEx(IntPtr p, IntPtr address,
        out Mbi info, IntPtr size);
    [DllImport("psapi", CharSet = CharSet.Unicode)]
    static extern int GetMappedFileName(IntPtr p, IntPtr address,
        StringBuilder name, int size);
    public static void List(int pid, string pattern)
    {
        IntPtr p = OpenProcess(0x0410, false, pid);  // QUERY, VM_READ
        long at = 0;
        Mbi m;
        string last = null;
        long sum = 0;
        while (VirtualQueryEx(p, (IntPtr)at, out m,
                   (IntPtr)Marshal.SizeOf(typeof(Mbi))) != IntPtr.Zero) {
            string name = null;
            if (m.type == 0x40000) {                 // MEM_MAPPED
                var s = new StringBuilder(1024);
                name = "(no name)";
                if (GetMappedFileName(p, m.baseAddress, s, 1024) > 0)
                    name = s.ToString();
            }
            if (name != last) {
                if (last != null && System.Text.RegularExpressions.Regex
                        .IsMatch(last, pattern))
                    Console.WriteLine("{0,12} bytes  {1}", sum, last);
                last = name;
                sum = 0;
            }
            sum += (long)m.regionSize;
            at = (long)m.baseAddress + (long)m.regionSize;
        }
    }
}
'@
[Mapped]::List($Id, $Pattern)
