#define _GNU_SOURCE
#include "runtime.h"
#include "gpu/bbgpu.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* The settings menu of the GPU library restarts through probe.c, which tests do not link. */
void runtime_restart(void) { abort(); }

/* Co-op (BB_ONLINE=1): the game's network and PSN imports resolve to the shadNet libraries of
 * the GPU library; trophies stay with the runtime. */
int main(void) {
    static const char *const online[]={
        "Nlev7Lg8k3A#E#F",  /* sceNetInit */
        "A9cVMUtEp4Y#K#L",  /* sceHttpInit */
        "hdpVEUDFW3s#L#M",  /* sceSslInit */
        "2rsFmlGWleQ#R#S",  /* sceNpCheckNpAvailability */
        "10t3e5+JPnU#P#Q",  /* sceNpMatching2Initialize */
        "3KOuC4RmZZU#T#U",  /* sceNpSignalingInitialize */
    };
    static const char *const local="XbkjbobZlCY#l#m"; /* sceNpTrophyCreateContext */
    setenv("BB_ONLINE","1",1);
    runtime_start(1);
    bbgpu_register_kernel();
    for (size_t i=0;i<sizeof(online)/sizeof(*online);++i) {
        uintptr_t address=runtime_resolve(online[i],0);
        if (!address || address!=bbgpu_resolve(online[i])) {
            printf("FAIL: %s (%s) is not the online version\n",online[i],runtime_import_name(online[i]));
            return 1;
        }
    }
    uintptr_t trophy=runtime_resolve(local,0);
    assert(trophy && trophy!=bbgpu_resolve(local));
    printf("PASS: online imports go to the shadNet libraries, trophies stay local\n");
    return 0;
}
