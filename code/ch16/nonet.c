/* Run a command with a seccomp filter that denies network sockets
   (Chapter 16).  usage: nonet COMMAND...
   socket() succeeds for AF_UNIX only; io_uring, which can open
   sockets without calling socket(), is denied as well.  */
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <sys/prctl.h>
#include <sys/socket.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <linux/audit.h>
#include <linux/filter.h>
#include <linux/seccomp.h>

#if defined(__x86_64__)
#define ARCH AUDIT_ARCH_X86_64
#elif defined(__aarch64__)
#define ARCH AUDIT_ARCH_AARCH64
#endif
#define LOAD(field) BPF_STMT(BPF_LD | BPF_W | BPF_ABS, \
                             offsetof(struct seccomp_data, field))
#define JUMP_IF(k, t, f) BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, (k), (t), (f))
#define RET(action) BPF_STMT(BPF_RET | BPF_K, (action))
#define DENY RET(SECCOMP_RET_ERRNO | EPERM)
#define ALLOW RET(SECCOMP_RET_ALLOW)

int main(int argc, char **argv)
{
    struct sock_filter filter[] = {
        LOAD(arch),                     /* another ABI: kill */
        JUMP_IF(ARCH, 1, 0), RET(SECCOMP_RET_KILL_PROCESS),
        LOAD(nr),
#ifdef __x86_64__                       /* x32 calls share the arch */
        BPF_JUMP(BPF_JMP | BPF_JGE | BPF_K, 0x40000000, 0, 1), DENY,
#endif
        JUMP_IF(__NR_io_uring_setup, 0, 1), DENY,
        JUMP_IF(__NR_socket, 1, 0), ALLOW,
        LOAD(args[0]),                  /* socket(domain, ...) */
        JUMP_IF(AF_UNIX, 0, 1), ALLOW,
        DENY,
    };
    struct sock_fprog prog = {
        sizeof filter / sizeof filter[0], filter };

    if (argc < 2 || prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) ||
        prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog)) {
        perror("nonet");
        return 1;
    }
    execvp(argv[1], argv + 1);
    perror(argv[1]);
    return 127;
}
