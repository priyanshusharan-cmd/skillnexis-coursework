CFLAGS = -std=gnu11 -O1 -Wall -Wextra -Werror
FREERTOS_TAG = V11.1.0
K = third_party/FreeRTOS-Kernel

all: build/test_agri build/agri_sim_shim

build:
	mkdir -p build results
build/test_agri: tests/test_agri.c common/agri.c common/agri.h | build
	gcc $(CFLAGS) -fsanitize=address,undefined -o $@ tests/test_agri.c common/agri.c
build/agri_sim_shim: sim/*.c sim/*.h app/*.c app/*.h common/agri.c sim/shim/* | build
	gcc $(CFLAGS) -pthread -Isim/shim -Isim -o $@ sim/main_sim.c sim/hal_sim.c app/app.c common/agri.c sim/shim/shim.c -lm

test: build/test_agri
	./build/test_agri

# quick: app tasks on a pthread stand-in for the FreeRTOS API
sim: build/agri_sim_shim
	./build/agri_sim_shim
	python3 sim/plot.py results/sim-3days.png

# the same app tasks on the real FreeRTOS kernel (POSIX port), fetched at a pinned release
$(K):
	git clone --depth 1 --branch $(FREERTOS_TAG) https://github.com/FreeRTOS/FreeRTOS-Kernel.git $(K)
build/agri_sim_freertos: $(K) sim/*.c app/*.c common/agri.c | build
	gcc -std=gnu11 -O1 -Wall -Wextra -Wno-unused-parameter -pthread -Isim -I$(K)/include -I$(K)/portable/ThirdParty/GCC/Posix \
	  -I$(K)/portable/ThirdParty/GCC/Posix/utils -o $@ sim/main_sim.c sim/hal_sim.c app/app.c common/agri.c \
	  $(K)/tasks.c $(K)/queue.c $(K)/list.c $(K)/event_groups.c $(K)/timers.c $(K)/portable/MemMang/heap_3.c \
	  $(K)/portable/ThirdParty/GCC/Posix/port.c $(K)/portable/ThirdParty/GCC/Posix/utils/wait_for_event.c -lm
sim-freertos: build/agri_sim_freertos
	./build/agri_sim_freertos

clean:
	rm -rf build
.PHONY: all test sim sim-freertos clean
