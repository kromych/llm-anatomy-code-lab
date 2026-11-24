// netjob.cs -- what a job's network rate control (the throttle that
// Gemini CLI sets) slows down.  netjob RATE N starts itself as a child in a
// job whose outgoing bandwidth is RATE bytes per second (0: no job), and
// the child sends N bytes to a loopback listener of the parent, resolves a
// name, and sends a HEAD request to example.org.
using System;
using System.Diagnostics;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

class NetJob
{
    [StructLayout(LayoutKind.Sequential)]
    struct NetRate { public ulong MaxBandwidth; public uint Flags;
                     public byte DscpTag; }
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool SetInformationJobObject(IntPtr job, int infoClass,
        ref NetRate info, int length);
    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    const int NetRateControl = 32;   // JobObjectNetRateControlInformation
    const uint Enable = 1, MaxBandwidth = 2;

    static string Ms(Stopwatch w)
    { return w.Elapsed.TotalMilliseconds.ToString("f0") + " ms"; }

    static int Main(string[] args)
    {
        if (args[0] == "child")
            return Child(int.Parse(args[1]), int.Parse(args[2]));
        ulong rate = ulong.Parse(args[0]);
        var listener = new TcpListener(IPAddress.Loopback, 0);
        listener.Start();
        int port = ((IPEndPoint)listener.LocalEndpoint).Port;
        var sink = new Thread(() => {
            var buf = new byte[65536];
            while (true) {
                var c = listener.AcceptTcpClient();
                var s = c.GetStream();
                try { while (s.Read(buf, 0, buf.Length) > 0) { } }
                catch (Exception) { }
                c.Close();
            }
        });
        sink.IsBackground = true;
        sink.Start();
        var psi = new ProcessStartInfo(
            Process.GetCurrentProcess().MainModule.FileName,
            "child " + port + " " + args[1]);
        psi.UseShellExecute = false;
        psi.RedirectStandardInput = true;
        var p = Process.Start(psi);
        if (rate > 0) {            // the child waits for "go" on stdin
            IntPtr job = CreateJobObject(IntPtr.Zero, null);
            var info = new NetRate { MaxBandwidth = rate,
                                     Flags = Enable | MaxBandwidth };
            if (!SetInformationJobObject(job, NetRateControl, ref info,
                                         Marshal.SizeOf(info)))
                Console.WriteLine("rate control failed, error " +
                                  Marshal.GetLastWin32Error());
            if (!AssignProcessToJobObject(job, p.Handle))
                Console.WriteLine("assign failed, error " +
                                  Marshal.GetLastWin32Error());
        }
        p.StandardInput.WriteLine("go");
        p.StandardInput.Close();
        p.WaitForExit();
        return p.ExitCode;
    }

    static int Child(int port, int n)
    {
        Console.In.ReadLine();
        var w = Stopwatch.StartNew();
        try {
            using (var c = new TcpClient("127.0.0.1", port)) {
                var s = c.GetStream();
                s.WriteTimeout = 20000;
                s.Write(new byte[n], 0, n);
            }
            Console.WriteLine("loopback: " + n + " bytes sent in " + Ms(w));
        } catch (Exception e) {
            Console.WriteLine("loopback: " + e.GetType().Name + " after " +
                              Ms(w));
        }
        w.Restart();
        try {
            var ips = Dns.GetHostAddresses("example.org");
            Console.WriteLine("dns: " + ips.Length + " addresses in " +
                              Ms(w));
        } catch (Exception e) {
            Console.WriteLine("dns: " + e.GetType().Name + " after " + Ms(w));
        }
        w.Restart();
        try {
            var c = new TcpClient();
            var ar = c.BeginConnect("example.org", 80, null, null);
            if (!ar.AsyncWaitHandle.WaitOne(20000)) {
                Console.WriteLine("http: no connection after " + Ms(w));
                return 0;
            }
            c.EndConnect(ar);
            var s = c.GetStream();
            s.WriteTimeout = s.ReadTimeout = 20000;
            byte[] req = Encoding.ASCII.GetBytes("HEAD / HTTP/1.1\r\n" +
                "Host: example.org\r\nConnection: close\r\n\r\n");
            s.Write(req, 0, req.Length);
            var buf = new byte[64];
            int k = s.Read(buf, 0, buf.Length);
            Console.WriteLine("http: " + req.Length + "-byte request, reply '" +
                Encoding.ASCII.GetString(buf, 0, Math.Min(k, 15)) +
                "' after " + Ms(w));
        } catch (Exception e) {
            Console.WriteLine("http: " + e.GetType().Name + " after " + Ms(w));
        }
        return 0;
    }
}
