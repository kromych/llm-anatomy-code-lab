#!/usr/bin/env python3
"""Run a command under a Landlock ruleset (Chapter 16).

usage: landlock.py [--ro PATH]... [--rw PATH]... -- COMMAND...

Files outside the listed paths can be neither read nor written.  From
ABI 4 on every TCP bind and connect is denied, from ABI 10 on UDP as
well, and from ABI 6 on signals and abstract Unix sockets cannot leave
the sandbox.  The ruleset binds this process and all its descendants.
"""
import ctypes
import os
import sys

CREATE, ADD, RESTRICT = 444, 445, 446      # same on x86_64 and arm64
PR_SET_NO_NEW_PRIVS = 38
FS_SINCE = [1] * 13 + [2, 3, 5, 9]         # ABI that brought each right
NET_SINCE = [4, 4, 10, 10]                 # TCP bind/connect, UDP
READ = 0b1101                              # execute, read file, read dir
FILE_RIGHTS = 0b111 | 1 << 14 | 1 << 15    # rights a file rule may hold
libc = ctypes.CDLL(None, use_errno=True)
u32, size = ctypes.c_uint32, ctypes.c_size_t


class RulesetAttr(ctypes.Structure):
    _fields_ = [("fs", ctypes.c_uint64), ("net", ctypes.c_uint64),
                ("scoped", ctypes.c_uint64)]


class PathBeneath(ctypes.Structure):     # the kernel reads 12 bytes
    _fields_ = [("allowed", ctypes.c_uint64), ("fd", ctypes.c_int32)]


def check(result):
    if result < 0:
        sys.exit("landlock: " + os.strerror(ctypes.get_errno()))
    return result


abi = check(libc.syscall(CREATE, None, size(0), u32(1)))
fs = sum(1 << i for i, v in enumerate(FS_SINCE) if abi >= v)
net = sum(1 << i for i, v in enumerate(NET_SINCE) if abi >= v)
attr = RulesetAttr(fs, net, 0b11 if abi >= 6 else 0)
ruleset = check(libc.syscall(CREATE, ctypes.byref(attr),
                             size(ctypes.sizeof(attr)), u32(0)))
args = sys.argv[1:]
while args[0] != "--":
    option, path, args = args[0], args[1], args[2:]
    allowed = READ if option == "--ro" else fs
    if not os.path.isdir(path):
        allowed &= FILE_RIGHTS
    rule = PathBeneath(allowed, os.open(path, os.O_PATH | os.O_CLOEXEC))
    check(libc.syscall(ADD, ruleset, 1, ctypes.byref(rule), u32(0)))
    os.close(rule.fd)
check(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0))
check(libc.syscall(RESTRICT, ruleset, u32(0)))
os.execvp(args[1], args[1:])
