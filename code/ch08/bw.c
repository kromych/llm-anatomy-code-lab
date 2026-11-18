/* bw.c THREADS -- read bandwidth: each thread sums its slice of a 1 GiB array */
#include <pthread.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#define N (1UL << 27)              /* 2^27 words of 8 bytes = 1 GiB */
static uint64_t *a; static int T; static uint64_t sums[64];
static void *run(void *p) {
    long t = (long)p; size_t lo = N / T * t, hi = N / T * (t + 1); uint64_t s = 0;
    for (int r = 0; r < 5; r++) for (size_t i = lo; i < hi; i++) s += a[i];
    sums[t] = s; return 0;
}
int main(int argc, char **argv) {
    T = atoi(argv[1]); a = malloc(N * 8);
    for (size_t i = 0; i < N; i++) a[i] = i;          /* touch every page */
    pthread_t th[64]; struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);
    for (long t = 0; t < T; t++) pthread_create(&th[t], 0, run, (void *)t);
    for (int t = 0; t < T; t++) pthread_join(th[t], 0);
    clock_gettime(CLOCK_MONOTONIC, &t1);
    double s = (t1.tv_sec - t0.tv_sec) + 1e-9 * (t1.tv_nsec - t0.tv_nsec);
    uint64_t x = 0; for (int t = 0; t < T; t++) x += sums[t];
    printf("threads %2d  %.1f GB/s  (check %llu)\n", T, 5.0 * N * 8 / s / 1e9, (unsigned long long)(x & 0xff));
    return 0;
}
