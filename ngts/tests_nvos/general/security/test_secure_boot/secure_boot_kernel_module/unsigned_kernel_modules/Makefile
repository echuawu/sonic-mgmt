obj-m += unsecure_kernel_module.o
all:
	make -C /lib/modules/5.10.0-12-2-amd64/build M=$(PWD) modules
clean:
	make -C /lib/modules/5.10.0-12-2-amd64/build M=$(PWD) modules
