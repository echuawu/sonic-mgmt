obj-m += secure_kernel_module.o
all:
	make -C /lib/modules/5.10.0-21-amd64/build M=$(PWD) modules
clean:
	make -C /lib/modules/5.10.0-21-amd64/build M=$(PWD) modules
