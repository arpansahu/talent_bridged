#!/bin/bash

# Function to execute a script and check if it was successful
execute_script() {
    local script=$1
    
    chmod +x "$script"
    ./"$script"
    
    # Check if the script was executed successfully
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to execute $script"
        exit 1
    fi
}

# Main script execution
main() {
    # Change to the directory where the script is located
    cd "$(dirname "$0")"
    
    # Execute convert_readme_to_html.sh
    execute_script "convert_readme_to_html.sh"
    
    # Execute upload_readme_html_to_arpansahu.sh
    execute_script "upload_readme_html_to_arpansahu.sh"
}

# Execute the main function
main "$@"