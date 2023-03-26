'''
This file includes the constants used
for secure boot testing
'''


class SecureBootConsts:
    '''
    class contains consts for secure boot
    '''
    ROOT_PRIVILAGE = 'sudo su'
    TMP_FOLDER = '/tmp'
    MOUNT_FOLDER = '/UEFI'
    IMAGE_PATH = ["non_secure_image_path", "sig_mismatch_image_path"]
    EFI_PARTITION_CMD = "fdisk -l | grep \"EFI System\" | awk \'{print $1}\'"
    LAST_OCCURENCE_REGEX = "({})(?!.*\1)"
    VMILUNZ_REGEX = '(vmlinuz-.*-amd64)'
    VMILUNZ_DIR = '/boot/'
    INVALID_SIGNATURE = ["Invalid signature detected",
                         "Malformed binary after Attribute Certificate Table",
                         "bad.*signature"]
    REBOOT = "sudo reboot -f"

    # numerical expressions
    SLEEP_AFTER_ONIE_INSTALL = 45
    SIG_START = -10
    SIG_END = -1

    FILE_DEFAULT_SCP_TIMEOUT = 240


class SonicSecureBootConsts(SecureBootConsts):
    '''
    class contains consts for secure boot
    '''
    SHIM = 'shim'
    GRUB = 'grub'
    VMLINUZ = 'vmlinuz'
    ORIGIN_TAG = '_origin'
    LOCAL_SECURE_BOOT_DIR = '/auto/sw_system_release/sonic/security/secure_boot'
    EFI_SECURE_COMPONENT = '{}/EFI/SONiC-OS/{}'
    SHIM_FILEPATH = EFI_SECURE_COMPONENT.format(SecureBootConsts.MOUNT_FOLDER, 'shimx64.efi')
    GRUB_FILEPATH = EFI_SECURE_COMPONENT.format(SecureBootConsts.MOUNT_FOLDER, 'grubx64.efi')
    KERNEL_MODULE_NAME = 'leds_mlxreg'
    KERNEL_MODULE_FILE = 'leds-mlxreg.ko'
    KERNEL_MODULE_TEMP_FILE_PATH = SecureBootConsts.TMP_FOLDER + '/' + KERNEL_MODULE_FILE
    USR_LIB_MODULES_PATH = '/usr/lib/modules'
    KERNEL_MODULE_BLOCK_MESSAGE = 'Key was rejected by service'
    INVALID_SIGNATURE = ["Invalid signature detected",
                         "Malformed binary after Attribute Certificate Table",
                         "bad.*signature",
                         "Key was rejected by service",
                         "CMS signature verification failed"]
    REBOOT = "sudo reboot -f"
    FAST_REBOOT = "sudo fast-reboot -f -d"
    WARM_REBOOT = "sudo warm-reboot -f -d"
    COLD_FAST_WARM_REBOOT_LIST = [REBOOT, FAST_REBOOT, WARM_REBOOT]

    SWITCH_RECOVER_TIMEOUT = 300
    ONIE_TIMEOUT = 120


class SecureUpgradeConsts:
    '''
    class contains consts for secure upgrade
    '''
    IMAGE_PATH = ("non_secure_image_path", "sig_mismatch_image_path")
    INVALID_SIGNATURE = "CMS signature Verification Failed"


class SonicSecureUpgradeConsts(SecureUpgradeConsts):
    '''
    class contains consts for secure upgrade
    '''
    pass
