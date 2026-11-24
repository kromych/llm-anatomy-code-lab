// xpc_rtt.swift -- round trip of a small message over XPC on macOS.
//
//   swiftc -O xpc_rtt.swift -o xpc_rtt && ./xpc_rtt 5000
//
// An anonymous NSXPCListener lives in this process and a connection is made
// to its endpoint; every message still travels as a Mach message through
// the kernel, as it would to a separate service. The client sends 64 bytes
// and waits for the reply; the output has the same columns as rtt.py.
import Foundation

@objc protocol Echo {
    func echo(_ data: Data, reply: @escaping (Data) -> Void)
}

final class EchoService: NSObject, Echo {
    func echo(_ data: Data, reply: @escaping (Data) -> Void) { reply(data) }
}

final class Delegate: NSObject, NSXPCListenerDelegate {
    func listener(_ listener: NSXPCListener,
                  shouldAcceptNewConnection c: NSXPCConnection) -> Bool {
        c.exportedInterface = NSXPCInterface(with: Echo.self)
        c.exportedObject = EchoService()
        c.resume()
        return true
    }
}

let n = CommandLine.arguments.count > 1 ? Int(CommandLine.arguments[1])! : 5000
let delegate = Delegate()
let listener = NSXPCListener.anonymous()
listener.delegate = delegate
listener.resume()

let conn = NSXPCConnection(listenerEndpoint: listener.endpoint)
conn.remoteObjectInterface = NSXPCInterface(with: Echo.self)
conn.resume()
let proxy = conn.synchronousRemoteObjectProxyWithErrorHandler { e in
    fatalError("XPC error: \(e)")
} as! Echo

let msg = Data(repeating: 0x78, count: 64)
func roundTrip() { proxy.echo(msg) { _ in } }   // synchronous proxy waits

for _ in 0..<200 { roundTrip() }
var t = [Double]()
t.reserveCapacity(n)
for _ in 0..<n {
    let a = DispatchTime.now().uptimeNanoseconds
    roundTrip()
    t.append(Double(DispatchTime.now().uptimeNanoseconds - a) / 1000)
}
t.sort()
func pct(_ q: Double) -> Double { t[min(t.count - 1, Int(q * Double(t.count)))] }
print(String(format: "xpc,%d,%.3f,%.3f,%.3f,NSXPCConnection to an anonymous listener",
             n, pct(0.5), pct(0.1), pct(0.9)))
