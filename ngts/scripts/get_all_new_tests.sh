#!/bin/bash

# Set the start and end date in YYYY-MM-DD format
start_date="$1"
end_date="$2"

# Set the file pattern to match
file_pattern=".*\/[^\/]*test[^\/]*.py"

# Set the directory to exclude (change 'exclude_dir' to the directory name you want to exclude)
exclude_dir="ngts"

mkdir /tmp/sonic-mgmt-get-new-tests && cd /tmp/sonic-mgmt-get-new-tests
git clone https://github.com/sonic-net/sonic-mgmt.git
cd sonic-mgmt



# Search for files that match the pattern and were added to Git within the date range
files=$(git log --after="$start_date" --before="$end_date" --name-status --pretty=format:"" |
  grep -E "^(A)\s+$file_pattern" |
  awk -v exclude_dir="$exclude_dir" '$2 !~ exclude_dir {print $2}')

# Initialize variables to store the maximum column widths
max_file_width=0
max_git_log_width=0

# Calculate the maximum column widths
for file in $files; do
  git_log=$(git log -n 1 --pretty=format:"%h | %an | %ad | %s" -- "$file")
  file_length=${#file}
  git_log_length=${#git_log}
  
  if [ "$file_length" -gt "$max_file_width" ]; then
    max_file_width=$file_length
  fi
  
  if [ "$git_log_length" -gt "$max_git_log_width" ]; then
    max_git_log_width=$git_log_length
  fi
done

# Print the table headers with the maximum widths
printf "%-${max_file_width}s | %-${max_git_log_width}s\n" "File Name" "Git Log"

# Iterate through the files and print the file name and the last Git log
for file in $files; do
  git_log=$(git log -n 1 --pretty=format:"%h | %an | %ad | %s" -- "$file")
  printf "%-${max_file_width}s | %-${max_git_log_width}s\n" "$file" "$git_log"
done

rm -rf /tmp/sonic-mgmt-get-new-tests
