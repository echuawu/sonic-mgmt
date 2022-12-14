#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kthread.h>
#include <linux/sched.h>
#include <linux/time.h>

int init_module(void)
{
    printk(KERN_INFO "Successful inserting of unsecure_kernel_module this a critical bug!\n");
    return 0;
}


void cleanup_module(void)
{
    printk(KERN_INFO "Unloading unsecure_kernel_module if it in case was inserted\n");
}
