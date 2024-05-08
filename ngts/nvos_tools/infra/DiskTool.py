import logging
from ngts.tools.test_utils import allure_utils as allure

logger = logging.getLogger()


class DiskTool:

    def __init__(self, engine, partition_name):
        self.engine = engine
        self.partition_name = partition_name

    def get_unmounted_partitions(self):
        # List all partitions and filter by partition name. Get only the names of unmounted partitions.
        with allure.step('List unmounted partitions'):
            unmounted_part_cmd = 'lsblk -rn -o NAME,MOUNTPOINT ' \
                                 '| grep {partition_name} ' \
                                 '| awk \'$1~/[[:digit:]]/ && $2 == ""\''.format(partition_name=self.partition_name)
            return self.engine.run_cmd(unmounted_part_cmd).split('\n')

    def mount_partitions(self, partitions):
        if not partitions:
            logger.info(f"No partitions provided")
            return
        with allure.step('Create folders and mount them'):
            for partition in partitions:
                if partition:
                    partition = partition.strip()
                    logger.info(f"Mount {partition}")
                    self.engine.run_cmd(f'mkdir tmp_{partition}')
                    self.engine.run_cmd(f'sudo mount /dev/{partition} tmp_{partition}')

    def unmount_partitions(self, unmounted_partitions):
        if not unmounted_partitions:
            logger.info(f"No partitions provided")
            return
        with allure.step('Unmount partition and remove created folders'):
            for partition in unmounted_partitions:
                if partition:
                    partition = partition.strip()
                    logger.info(f"Unmount {partition}")
                    self.engine.run_cmd(f'sudo umount /dev/{partition}')
                    self.engine.run_cmd(f'rm -r tmp_{partition}')

    def get_available_partition_capacity(self):
        with allure.step('Get the available storage percent output'):
            # The fifth column contains the Usage in percent for disk free tool
            cmd = 'df -H | grep {partition_name} | tr -s " " | cut -d" " -f5'.format(
                partition_name=self.partition_name)
            output = self.engine.run_cmd(cmd)
            available_disk_storages = output.split('\n')
            return available_disk_storages

    @staticmethod
    def get_path_available_capacity_percentage(engine, path):
        return engine.run_cmd(f"df -h {path}" + " | awk 'NR==2 {sub(/%/,\"\",$5); print $5}'")
