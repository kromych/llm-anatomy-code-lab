// Start a command in a Windows sandbox (Chapter 16), in C# 5 for
// PowerShell 5.1's Add-Type.
//   sbx MODE [--job] [--tree] [--sid SID] -- COMMAND LINE
//     none           an ordinary child process
//     restricted     a write-restricted token: a write must also be
//                    granted to SID (or to Everyone)
//     lowil          a token at low integrity level
//     appcontainer   AppContainer SID, no capabilities; the SID is
//                    also let into our window station and desktop
//     --job          a job object that admits one process only
//     --tree         a job object without that limit; like --job, it
//                    ends its processes when this launcher exits
//   sbx mkprofile NAME    create an AppContainer profile, print its SID
//   sbx rmprofile NAME    delete it
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;

static class Sbx
{
    [StructLayout(LayoutKind.Sequential)]
    struct StartupInfoEx
    {
        public int cb;
        public IntPtr reserved, desktop, title;
        public int x, y, width, height, columns, rows, fill, flags;
        public short show, reserved2;
        public IntPtr reserved3, stdIn, stdOut, stdErr;
        public IntPtr attributes;               // the EX part
    }

    [StructLayout(LayoutKind.Sequential)]
    struct ProcessInfo
    {
        public IntPtr process, thread;
        public int pid, tid;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct SidAndAttributes { public IntPtr sid; public uint attributes; }

    [StructLayout(LayoutKind.Sequential)]
    struct SecurityCapabilities
    {
        public IntPtr appContainerSid, capabilities;
        public uint count, reserved;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct JobLimits                            // ..._EXTENDED_LIMIT_...
    {
        public long processTime, jobTime;
        public uint flags;
        public UIntPtr minWorkingSet, maxWorkingSet;
        public uint activeProcesses;
        public UIntPtr affinity;
        public uint priority, scheduling;
        public ulong io1, io2, io3, io4, io5, io6;
        public UIntPtr processMemory, jobMemory, peakProcess, peakJob;
    }

    [StructLayout(LayoutKind.Sequential)]
    struct ExplicitAccess                       // EXPLICIT_ACCESS + TRUSTEE
    {
        public uint rights;
        public int mode, inheritance;
        public IntPtr multiple;
        public int operation, form, type;
        public IntPtr sid;
    }

    const string A = "advapi32", K = "kernel32", U = "userenv",
        W = "user32";
    const uint DISABLE_MAX_PRIVILEGE = 1, LUA_TOKEN = 4,
        WRITE_RESTRICTED = 8, CREATE_SUSPENDED = 4,
        EXTENDED_STARTUPINFO = 0x80000, KILL_ON_JOB_CLOSE = 0x2000,
        ACTIVE_PROCESS = 8;

    [DllImport(K)] static extern IntPtr GetCurrentProcess();
    [DllImport(K)] static extern IntPtr GetStdHandle(int which);
    [DllImport(K)] static extern int ResumeThread(IntPtr thread);
    [DllImport(K)] static extern int WaitForSingleObject(IntPtr h, int ms);
    [DllImport(K)] static extern bool GetExitCodeProcess(IntPtr p,
        out int code);
    [DllImport(A, SetLastError = true)]
    static extern bool OpenProcessToken(IntPtr process, uint access,
        out IntPtr token);
    [DllImport(A, SetLastError = true)]
    static extern bool CreateRestrictedToken(IntPtr token, uint flags,
        uint nDisable, IntPtr disable, uint nDelete, IntPtr delete,
        uint nRestrict, SidAndAttributes[] restrict, out IntPtr result);
    [DllImport(A, SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool ConvertStringSidToSid(string s, out IntPtr sid);
    [DllImport(A, SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool ConvertSidToStringSid(IntPtr sid, out IntPtr s);
    [DllImport(A)] static extern int GetLengthSid(IntPtr sid);
    [DllImport(A, SetLastError = true)]
    static extern bool SetTokenInformation(IntPtr token, int infoClass,
        ref SidAndAttributes label, int size);
    [DllImport(A, SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool CreateProcessAsUser(IntPtr token, string app,
        string cmd, IntPtr pa, IntPtr ta, bool inherit, uint flags,
        IntPtr env, string cwd, ref StartupInfoEx si, out ProcessInfo pi);
    [DllImport(K, SetLastError = true, CharSet = CharSet.Unicode)]
    static extern bool CreateProcess(string app, string cmd, IntPtr pa,
        IntPtr ta, bool inherit, uint flags, IntPtr env, string cwd,
        ref StartupInfoEx si, out ProcessInfo pi);
    [DllImport(K, SetLastError = true)]
    static extern bool InitializeProcThreadAttributeList(IntPtr list,
        int count, int flags, ref IntPtr size);
    [DllImport(K, SetLastError = true)]
    static extern bool UpdateProcThreadAttribute(IntPtr list, uint flags,
        IntPtr attribute, IntPtr value, IntPtr size, IntPtr prev,
        IntPtr retSize);
    [DllImport(U, CharSet = CharSet.Unicode)]
    static extern int CreateAppContainerProfile(string name,
        string display, string description, IntPtr caps, int count,
        out IntPtr sid);
    [DllImport(U, CharSet = CharSet.Unicode)]
    static extern int DeriveAppContainerSidFromAppContainerName(
        string name, out IntPtr sid);
    [DllImport(U, CharSet = CharSet.Unicode)]
    static extern int DeleteAppContainerProfile(string name);
    [DllImport(K, SetLastError = true)]
    static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport(K, SetLastError = true)]
    static extern bool SetInformationJobObject(IntPtr job, int infoClass,
        ref JobLimits limits, int size);
    [DllImport(K, SetLastError = true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr p);
    [DllImport(K)] static extern int GetCurrentThreadId();
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
    [DllImport(A)]
    static extern int SetEntriesInAcl(int count, ref ExplicitAccess entry,
        IntPtr old, out IntPtr result);
    [DllImport(A)]
    static extern int SetSecurityInfo(IntPtr h, int type, int info,
        IntPtr owner, IntPtr group, IntPtr dacl, IntPtr sacl);

    static void Check(bool ok, string what)
    {
        if (!ok)
            throw new Win32Exception(Marshal.GetLastWin32Error(), what);
    }

    static IntPtr Sid(string text)
    {
        IntPtr sid;
        Check(ConvertStringSidToSid(text, out sid), text);
        return sid;
    }

    static int Profile(string verb, string name)
    {
        if (verb == "rmprofile")
            return DeleteAppContainerProfile(name);
        IntPtr sid, text;
        if (CreateAppContainerProfile(name, name, name, IntPtr.Zero, 0,
                                      out sid) < 0)     // already there
            DeriveAppContainerSidFromAppContainerName(name, out sid);
        ConvertSidToStringSid(sid, out text);
        Console.WriteLine(Marshal.PtrToStringUni(text));
        return 0;
    }

    // Add an ACE for sid to a window station or desktop, which user32
    // must open in every process.  Without it, programs that load
    // user32 (.NET, PowerShell, whoami) fail with DLL_INIT_FAILED.
    static void LetIn(IntPtr current, bool desktop, IntPtr sid)
    {
        var name = new StringBuilder(256);
        int needed;
        GetUserObjectInformation(current, 2, name, 512, out needed);
        const uint DAC = 0x60000;               // READ_CONTROL, WRITE_DAC
        IntPtr h = desktop ? OpenDesktop(name.ToString(), 0, false, DAC)
                           : OpenWindowStation(name.ToString(), false, DAC);
        Check(h != IntPtr.Zero, name.ToString());
        IntPtr dacl, descriptor, result;
        var entry = new ExplicitAccess {
            rights = 0x10000000, mode = 1, sid = sid };   // GENERIC_ALL
        Check(GetSecurityInfo(h, 7, 4, IntPtr.Zero, IntPtr.Zero, out dacl,
                  IntPtr.Zero, out descriptor) == 0 &&
              SetEntriesInAcl(1, ref entry, dacl, out result) == 0 &&
              SetSecurityInfo(h, 7, 4, IntPtr.Zero, IntPtr.Zero, result,
                  IntPtr.Zero) == 0, name.ToString());
    }

    // Give the child the security capabilities of an AppContainer.
    static void AppContainer(ref StartupInfoEx si, string sid)
    {
        var caps = new SecurityCapabilities { appContainerSid = Sid(sid) };
        LetIn(GetProcessWindowStation(), false, caps.appContainerSid);
        LetIn(GetThreadDesktop(GetCurrentThreadId()), true,
              caps.appContainerSid);
        IntPtr p = Marshal.AllocHGlobal(Marshal.SizeOf(caps)),
               size = IntPtr.Zero;
        Marshal.StructureToPtr(caps, p, false);
        InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref size);
        si.attributes = Marshal.AllocHGlobal(size);
        Check(InitializeProcThreadAttributeList(si.attributes, 1, 0,
                                                ref size), "attributes");
        Check(UpdateProcThreadAttribute(si.attributes, 0,
                (IntPtr)0x20009,        // ..._SECURITY_CAPABILITIES
                p, (IntPtr)Marshal.SizeOf(caps), IntPtr.Zero,
                IntPtr.Zero), "security capabilities");
        si.cb = Marshal.SizeOf(si);
    }

    // A restricted copy of our own token.
    static IntPtr Token(string mode, string sid)
    {
        IntPtr token, result;
        Check(OpenProcessToken(GetCurrentProcess(), 0xF01FF, out token),
              "OpenProcessToken");
        if (mode == "restricted") {
            LetIn(GetProcessWindowStation(), false, Sid(sid));
            LetIn(GetThreadDesktop(GetCurrentThreadId()), true, Sid(sid));
            var restrict = new[] {
                new SidAndAttributes { sid = Sid(sid) },
                new SidAndAttributes { sid = Sid("S-1-1-0") } };
            Check(CreateRestrictedToken(token, DISABLE_MAX_PRIVILEGE |
                      LUA_TOKEN | WRITE_RESTRICTED, 0, IntPtr.Zero, 0,
                      IntPtr.Zero, 2, restrict, out result),
                  "CreateRestrictedToken");
        } else {                                // lowil
            Check(CreateRestrictedToken(token, DISABLE_MAX_PRIVILEGE, 0,
                      IntPtr.Zero, 0, IntPtr.Zero, 0, null, out result),
                  "CreateRestrictedToken");
            var label = new SidAndAttributes {
                sid = Sid("S-1-16-4096"), attributes = 0x20 };
            Check(SetTokenInformation(result, 25, ref label,
                      Marshal.SizeOf(label) + GetLengthSid(label.sid)),
                  "SetTokenInformation");
        }
        return result;
    }

    static int Main(string[] args)
    {
        if (args[0].EndsWith("profile"))
            return Profile(args[0], args[1]);
        string mode = args[0], sid = null;
        bool job = false, tree = false;
        int i = 1;
        for (; args[i] != "--"; i++) {
            if (args[i] == "--job") job = true;
            else if (args[i] == "--tree") tree = true;
            else if (args[i] == "--sid") sid = args[++i];
        }
        string cmd = string.Join(" ", args, i + 1, args.Length - i - 1);
        var si = new StartupInfoEx();
        si.cb = Marshal.SizeOf(si) - IntPtr.Size;   // a plain STARTUPINFO
        si.flags = 0x100;                           // use our std handles
        si.stdIn = GetStdHandle(-10);
        si.stdOut = GetStdHandle(-11);
        si.stdErr = GetStdHandle(-12);
        uint flags = CREATE_SUSPENDED;
        ProcessInfo pi;
        if (mode == "appcontainer") {
            AppContainer(ref si, sid);
            flags |= EXTENDED_STARTUPINFO;
        }
        if (mode == "none" || mode == "appcontainer")
            Check(CreateProcess(null, cmd, IntPtr.Zero, IntPtr.Zero, true,
                      flags, IntPtr.Zero, null, ref si, out pi),
                  "CreateProcess");
        else
            Check(CreateProcessAsUser(Token(mode, sid), null, cmd,
                      IntPtr.Zero, IntPtr.Zero, true, flags, IntPtr.Zero,
                      null, ref si, out pi), "CreateProcessAsUser");
        if (job || tree) {          // before the child runs a single step
            IntPtr j = CreateJobObject(IntPtr.Zero, null);
            var limits = new JobLimits { flags = KILL_ON_JOB_CLOSE };
            if (job) {
                limits.flags |= ACTIVE_PROCESS;
                limits.activeProcesses = 1;
            }
            Check(SetInformationJobObject(j, 9, ref limits,
                      Marshal.SizeOf(limits)), "job limits");
            Check(AssignProcessToJobObject(j, pi.process), "job");
        }
        ResumeThread(pi.thread);
        WaitForSingleObject(pi.process, -1);
        int code;
        GetExitCodeProcess(pi.process, out code);
        return code;
    }
}
