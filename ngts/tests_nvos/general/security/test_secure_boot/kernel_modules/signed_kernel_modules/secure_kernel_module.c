#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/sched.h>
#include <linux/time.h>

int init_module(void)
{
    printk(KERN_INFO "Successful inserting of secure_kernel_module as expected\n");
    return 0;
}


void cleanup_module(void)
{
    printk(KERN_INFO "Unloading secure_kernel_module\n");
}
