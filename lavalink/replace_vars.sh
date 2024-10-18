#!/bin/bash

# Check if a filename was provided
if [ -z "$1" ]; then
  echo "Usage: $0 filename"
  exit 1
fi

# Assign the first argument to the FILE variable
FILE="$1"

# List of variable names to replace
VARIABLES=("PO_TOKEN" "VISITOR_DATA")

# Loop through each variable
for VAR in "${VARIABLES[@]}"; do
  # Use indirect reference to get the value of the variable
  VALUE="${!VAR}"

  # Replace ${{ VAR }} with the value of the environment variable in the file
  sed -i "s|\${{ $VAR }}|$VALUE|g" "$FILE"
done

echo "All variables have been replaced in $FILE."
