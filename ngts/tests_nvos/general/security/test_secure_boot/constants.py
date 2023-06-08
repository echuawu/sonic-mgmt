'''
This file includes the constants used
for secure boot testing
'''


class SecureBootConsts:
    '''
    class contains commands and consts
    '''
    ROOT_PRIVILAGE = 'sudo su'
    TMP_FOLDER = '/tmp'
    MOUNT_FOLDER = '/UEFI'
    EFI_PARTITION_CMD = "fdisk -l | grep \"EFI System\" | awk \'{print $1}\'"
    LAST_OCCURENCE_REGEX = "({})(?!.*\1)"
    LOCAL_SECURE_BOOT_DIR = '/auto/sw_system_project/NVOS_INFRA/security/verification/secure_boot'
    EFI_SECURE_COMPONENT = '{}/EFI/nvos/{}'
    SHIM_FILEPATH = EFI_SECURE_COMPONENT.format(MOUNT_FOLDER, 'shimx64.efi')
    GRUB_FILEPATH = EFI_SECURE_COMPONENT.format(MOUNT_FOLDER, 'grubx64.efi')
    VMLINUZ_REGEX = '(vmlinuz-.*-amd64)'
    VMLINUZ_DIR = '/boot/'
    INVALID_SIGNATURE = ["Invalid signature detected",
                         "Malformed binary after Attribute Certificate Table",
                         "bad.*signature"]
    REBOOT_CMD = "sudo reboot -f"

    # numerical expressions
    SLEEP_AFTER_ONIE_INSTALL = 45
    SIG_START = -10
    SIG_END = -1

    FILE_DEFAULT_SCP_TIMEOUT = 240
