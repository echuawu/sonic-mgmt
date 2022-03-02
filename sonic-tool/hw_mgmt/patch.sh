#!/usr/bin/env bash

# Usage: linux$ ./patch.sh "[patch description]"

# commit is the commit in the mellanox branch that you wish to revise.

# 1. Ensture that the main hw-mgmt script has run at least once (mellanox branch is rebased on sonic)
# 2. Navigate to the linux directory
# 3. git checkout the commit you wish to modify
# 4. Make any changes and git add them
# 5. Run this script to automatically regenerate the patches and generate a patch file for future use

PATCHES="patch/master"


# Create a new branch for us to work with
git branch patch-1
git branch patch-2
git checkout patch-1


# Ammend the commit
git commit --amend --no-edit


# Rebase
git rebase patch-2 mellanox --onto patch-1


# Clean up
git branch -D patch-1
git branch -D patch-2


# Regenerate patches into new folder
rm -rf patch-2
mkdir patch-2
cd patch-2
git format-patch sonic..mellanox | while read x; do mv "$x" $(echo "$x" | cut -d '-' -f2-); done
sed -i 's/\[PATCH.*\] //g' ./*.patch
sed -i '1d' ./*.patch


# Create patch file from one patch set to the other
cd ..
git diff -b -w --ignore-space-at-eol --ignore-cr-at-eol --no-index patch patch-2 > $1.patch
mv patch-2 patch


echo "Created $1.patch please review (you likely need to remove some redundant diffs) and copy to patch directory as needed."


# Update sonic-linux-kernel
cd ..
cp linux/patch/*.patch sonic-linux-kernel/patch/
python ../sonic_series.py export
