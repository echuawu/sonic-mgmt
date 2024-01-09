#!/bin/bash

# Default value for age_in_hours
age_in_hours = 23  # Default age if the flag is not provided

while getopts "a:" flag; do
    case "${flag}" in
        a) age_in_hours=${OPTARG};;
    esac
done

# Get the list of running containers with their status
containers_info=$(docker ps --format '{{.ID}}|{{.Status}}|{{.Image}}')

# Check if containers_info is empty or has no line breaks (single line)
if [ -z "$containers_info" ]; then
    echo "No running containers found."
    exit 0  # Exit script gracefully
fi

# Get the current time in seconds since epoch
current_time=$(date +%s)

# Calculate age_in_sec based on provided age_in_hours
age_in_sec=$((age_in_hours * 60 * 60))

# Loop through each container
echo "$containers_info" | while IFS='|' read -r container_id container_status container_image; do
    # Check if the container status indicates 'Up' and the container image is related to sonic
    if [[ "$container_status" == *Up* ]] && { [[ "$container_image" == *"sonic"* ]] || [[ "$container_image" == *"simx"* ]]; }; then
        # Get the container uptime
        container_uptime=$(docker inspect -f '{{ .State.StartedAt }}' "$container_id")
        container_uptime_seconds=$(date -d "$container_uptime" +%s)

        # Calculate the time the container has been running
        uptime_difference=$((current_time - container_uptime_seconds))

        # Check if the container has been running for more than specified hours
        if (( uptime_difference > age_in_sec )); then
            # Stop the container
            docker stop "$container_id"
        fi
    fi
done

# Prune stopped containers to reclaim space
docker container prune -f
