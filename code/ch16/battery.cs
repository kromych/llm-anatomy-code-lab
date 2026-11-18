// The battery of battery.py for Windows (Chapter 16), in C# 5 so that
// PowerShell 5.1 can compile it.  usage: battery ROOT PORT
//                                        battery listen PORTFILE LOG
//                                        battery linger MARKER
using System;
using System.Diagnostics;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Text;

static class Battery
{
    static string root;
    static int port;

    static void Control()       // write inside the workspace
    {
        File.WriteAllText(root + @"\work\ok.txt", "ok");
    }

    static void Write()         // write outside it
    {
        File.WriteAllText(root + @"\outside\probe.txt", "escaped");
    }

    static void Read()          // read the dummy secret
    {
        File.ReadAllText(root + @"\secret\token.txt");
    }

    static void Net()
    {
        using (var c = new TcpClient()) {
            if (!c.ConnectAsync("127.0.0.1", port).Wait(3000))
                throw new TimeoutException();
            var buf = new byte[64];
            int n = c.GetStream().Read(buf, 0, buf.Length);
            if (!Encoding.ASCII.GetString(buf, 0, n).StartsWith("battery"))
                throw new IOException("not our listener");
        }
    }

    static void Spawn()
    {
        var p = Process.Start(new ProcessStartInfo(
            Environment.SystemDirectory + @"\cmd.exe", "/c exit 0")
            { UseShellExecute = false });
        p.WaitForExit();
    }

    static void Hook()          // write a git hook inside the workspace
    {
        File.WriteAllText(root + @"\work\.git\hooks\pre-commit", "escaped");
    }

    static void Orphan()        // leave a copy of ourselves behind
    {
        Process.Start(new ProcessStartInfo(
            typeof(Battery).Assembly.Location,
            "linger \"" + root + @"\work\orphan.txt" + "\"")
            { UseShellExecute = false });
    }

    static void Linger(string marker)   // the child: still alive later?
    {
        System.Threading.Thread.Sleep(1000);
        File.WriteAllText(marker, "alive");
    }

    static void Probe(string name, Action probe)
    {
        try {
            probe();
            Console.WriteLine("{0,-8}ALLOWED", name);
        } catch (Exception e) {
            while (e.InnerException != null) e = e.InnerException;
            Console.WriteLine("{0,-8}BLOCKED  {1}", name, e.GetType().Name);
        }
    }

    static void Listen(string portFile, string log)
    {
        var srv = new TcpListener(IPAddress.Loopback, 0);
        srv.Start();
        File.WriteAllText(portFile,
            ((IPEndPoint)srv.LocalEndpoint).Port.ToString());
        while (true) {
            using (var c = srv.AcceptTcpClient()) {
                var hello = Encoding.ASCII.GetBytes("battery-listener\n");
                c.GetStream().Write(hello, 0, hello.Length);
                File.AppendAllText(log, c.Client.RemoteEndPoint + "\n");
            }
        }
    }

    static void Main(string[] args)
    {
        if (args[0] == "listen") { Listen(args[1], args[2]); return; }
        if (args[0] == "linger") { Linger(args[1]); return; }
        root = args[0];
        port = int.Parse(args[1]);
        Probe("control", Control);
        Probe("write", Write);
        Probe("read", Read);
        Probe("net", Net);
        Probe("spawn", Spawn);
        Probe("hook", Hook);
        Probe("orphan", Orphan);
    }
}
