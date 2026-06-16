#include <stdio.h>
#include <sys/utsname.h>
#include <unistd.h>

int main(void) {
    struct utsname info;

    puts("Hello from C on Luckfox PicoCalc");
    printf("uid: %ld\n", (long)getuid());

    if (uname(&info) == 0) {
        printf("sysname: %s\n", info.sysname);
        printf("machine: %s\n", info.machine);
        printf("release: %s\n", info.release);
    }

    return 0;
}
