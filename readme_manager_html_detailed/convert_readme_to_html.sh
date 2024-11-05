#!/bin/bash

# Define the URL to the GitHub repository and the files to download
REPO_URL="https://raw.githubusercontent.com/arpansahu/common_readme/main"
FILES=("requirements.txt" "convert_readme_to_html.py")
EXTRA_FILES=("Readme_converted.md") # Add any extra files here

# Function to download files
download_files() {
    echo "Downloading Required files..."
    for file in "${FILES[@]}"; do
        curl -O "$REPO_URL/readme_manager_html_detailed/$file"
        # Check if the file was downloaded successfully
        if [[ $? -ne 0 ]]; then
            echo "Error: Failed to download $file"
            exit 1
        fi
    done
}

# Create and activate virtual environment
create_and_activate_env() {
    echo "Creating and activating virtual environment"
    python3 -m venv env
    source env/bin/activate
}

# Install requirements
install_requirements() {
    echo "Installing python requirements"
    pip install -r requirements.txt
}

# Run convert_readme_to_html.py
run_readme_to_html_generator() {
    echo "Running run_readme_to_html_generator python file"
    python convert_readme_to_html.py
}

# Deactivate and delete the environment
cleanup_env() {
    echo "Cleaning up environment..."
    deactivate
    rm -rf env
}

# Delete downloaded files
delete_downloaded_and_extra_files() {
    echo "Deleting downloaded and extra files..."
    local all_files=("${FILES[@]}" "${EXTRA_FILES[@]}")
    for file in "${all_files[@]}"; do
        rm -f "$file"
    done
}

# Main script execution
main() {
    # Change to the directory where the script is located
    cd "$(dirname "$0")"
    
    # Determine the environment
    ENVIRONMENT=${1:-prod}
    
    download_files
    create_and_activate_env
    install_requirements
    run_readme_to_html_generator
    cleanup_env
    delete_downloaded_and_extra_files
}

# Execute the main function with provided arguments or default to prod environment
main "$@"