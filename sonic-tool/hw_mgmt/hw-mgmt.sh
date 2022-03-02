#!/usr/bin/env bash

SONIC_VERSION=hwmgmt_7202
SONIC_LINUX=v5.10.46
SONIC_REPO=git@github.com:alexrallen/sonic-linux-kernel.git

HWMGMT_VERSION=V.7.0020.1300_BR
HWMGMT_LINUX=v5.10.43
HWMGMT_REPO=https://github.com/Mellanox/hw-mgmt

# Overrides patches even if they don't have an upstream commit
OVERRIDE="0053,0054"

# Location of "local" patches we need on top of hw-mgmt patches for SONiC compatibility
PATCHES="patch/master"

if [ "$1" != "resume" ]; then

# Clear and create work directory
rm -rf work
mkdir work
cd work


# Clone repositories (cache a linux directory to clone from for future runs for speed)
[ -d "../linux" ] || git clone https://github.com/gregkh/linux ../linux
git clone ../linux linux
git clone $HWMGMT_REPO
git clone $SONIC_REPO


# Checkout repos
cd linux
git checkout $HWMGMT_LINUX
cd ..

cd hw-mgmt
git checkout $HWMGMT_VERSION
cd ..

cd sonic-linux-kernel
git checkout $SONIC_VERSION
cd ..

fi


echo "Cloned down. Make any changes and press any key to continue...."
echo "You may also exit via Ctl-C and resume via ./hw-mgmt resume"
read -n 1 -s


# Create patch folder for hw-mgmt
cd linux
mkdir hw-mgmt
cd ..

# Checkout master version of patch status table
cd hw-mgmt
git checkout master -- recipes-kernel/linux/Patch_Status_Table.txt
cd ..

# Generate hw-mgmt patch set
python ../hwmgmt_series.py $HWMGMT_LINUX $OVERRIDE


# Import hw-mgmt patches on top of target version
cd linux
git branch mellanox
git checkout mellanox
sed -i '1d' ./hw-mgmt/*.patch
python ../../name_patches.py
stg init
stg import -s hw-mgmt/series


# Now setup SONiC environment
git checkout $SONIC_LINUX
mkdir sonic
cd ..

cp sonic-linux-kernel/patch/*.patch linux/sonic/

python ../sonic_series.py


# Import sonic patches on top of target version
cd linux
git branch sonic
git checkout sonic
stg init
stg import -s sonic/series


# Perform rebase
git rebase $HWMGMT_LINUX mellanox --onto sonic


# Generate patches
mkdir patch
cd patch
git format-patch sonic..mellanox | while read x; do mv "$x" $(echo "$x" | cut -d '-' -f2-); done
sed -i 's/\[PATCH.*\] //g' ./*.patch
sed -i '1d' ./*.patch


# Apply local patches
for i in ../../../$PATCHES/*.patch; do patch -p2 < $i; done
rm -rf ./*.orig
cd ../..


# Upload to sonic-linux-kernel
cp linux/patch/*.patch sonic-linux-kernel/patch/
python ../sonic_series.py export


# Sync local environment to local patches
cd linux/patch
ls > ../series
mv ../series .

git checkout sonic
git branch -D mellanox
git branch mellanox
git checkout mellanox

#stg branch --cleanup --force
#stg init
#stg import -s series
git am $(cat series)
rm -rf series
