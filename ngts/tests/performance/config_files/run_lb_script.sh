#!/bin/bash

set -x

# Check if log port argument is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <initial_hex_value>"
    exit 1
fi

# Initialize log port with the provided argument
X=$1


check_rc()
{
  rc=$?
  if  [ $rc -ne 0 ]; then
    echo "$1";
    exit $1;
  fi
}


# Run the loop 64 times
for (( i=0; i<64; i++ )); do
    # Convert X to hexadecimal string
    hex_X=$(printf '%#x' "$X")

    # Run the command with updated value of X
    yes y | sx_api_port_state_set.py --log_port "$hex_X" --state down
    check_rc  'ERROR: Shuting down the port has failed' 1
    sx_api_port_phys_loopback.py --cmd 0 --log_port "$hex_X" --loopback_type 2 --force
    check_rc  'ERROR: Setting loopback on the port has  failed' 1
    python api_for_filter.py --log_port "$hex_X"
    check_rc  'ERROR: Setting loopback filter on the port has failed' 1
    yes y | sx_api_port_state_set.py --log_port "$hex_X" --state up
    check_rc  'ERROR: Starting up the port has failed' 1

    # Increment X by 2 for the next iteration
    ((X+=2))
done
