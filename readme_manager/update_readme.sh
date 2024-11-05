#!/bin/bash

# Define the URL to the GitHub repository and the files to download
REPO_URL="https://raw.githubusercontent.com/arpansahu/common_readme/main"
FILES=("requirements.txt" "readme_updater.py" "baseREADME.md" "include_files.py")

# Function to download files
download_files() {
    for file in "${FILES[@]}"; 
    do
        curl -O "$REPO_URL/$file"
        # Check if the file was downloaded successfully
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to download $file"
            exit 1
        fi
    done
}

# Create and activate virtual environment
create_and_activate_env() {
    python3 -m venv env
    source env/bin/activate
}

# Install requirements
install_requirements() {
    pip install -r requirements.txt
}

# Run readme_updater.py
run_readme_updater() {
    python readme_updater.py
}

# Deactivate and delete the environment
cleanup_env() {
    deactivate
    rm -rf env
}

# Delete downloaded files
delete_downloaded_files() {
    for file in "${FILES[@]}"; 
    do
        rm -f "$file"
    done
}

# Main script execution
main() {
    # Change to the directory where the script is located
    cd "$(dirname "$0")"
    download_files
    create_and_activate_env
    install_requirements
    run_readme_updater
    cleanup_env
    delete_downloaded_files
}

# Execute the main function
main