#!/bin/bash

# Script to remove trailing spaces from all relevant files in the project
# Usage: ./remove_trailing_spaces.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting trailing space removal...${NC}"

# Create temporary files to store counts
processed_file=$(mktemp)
modified_file=$(mktemp)
echo "0" > "$processed_file"
echo "0" > "$modified_file"

# Find all relevant files and process them
find . -type f \
    ! -path "*/\.*" \
    ! -path "*/build/*" \
    ! -path "*/third_party/*" \
    ! -path "*/_dataset/*" \
    ! -path "*/venv/*" \
    \( -name "*.cc" -o -name "*.h" -o -name "*.md" -o -name "*.txt" -o -name "*.py" -o -name "*.sh" \) \
    -print0 | while IFS= read -r -d '' file; do

    # Skip binary files
    if file "$file" | grep -q "binary file"; then
        continue
    fi

    # Increment processed count
    processed=$(cat "$processed_file")
    processed=$((processed + 1))
    echo "$processed" > "$processed_file"

    # Create a temporary file
    temp_file=$(mktemp)
    cp "$file" "$temp_file"

    # Remove trailing spaces
    if sed -i '' 's/ *$//' "$file" 2>/dev/null; then
        # Check if the file was actually modified
        if ! cmp -s "$file" "$temp_file"; then
            modified=$(cat "$modified_file")
            modified=$((modified + 1))
            echo "$modified" > "$modified_file"
            echo -e "${GREEN}Modified:${NC} $file"
        fi
    else
        echo -e "${RED}Error processing:${NC} $file"
    fi

    # Clean up temporary file
    rm "$temp_file"
done

# Read final counts
processed=$(cat "$processed_file")
modified=$(cat "$modified_file")

# Clean up temporary count files
rm "$processed_file" "$modified_file"

echo -e "\n${YELLOW}Summary:${NC}"
echo -e "Total files processed: $processed"
echo -e "Files modified: $modified"
echo -e "${GREEN}Trailing space removal completed!${NC}"