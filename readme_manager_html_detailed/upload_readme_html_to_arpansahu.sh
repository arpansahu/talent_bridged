#!/bin/bash

# Define variables
TARGET_REPO_URL="https://github.com/arpansahu/arpansahu_dot_me.git"
COMMIT_MESSAGE="Automatic Update readme.html"
RELATIVE_PATH="templates/modules/project_detailed/project_partials/talent_bridged/"

# Function to extract the repository name from the URL
extract_repo_name() {
    basename -s .git "$TARGET_REPO_URL"
}

# Clone the target repository
clone_target_repo() {
    local repo_name
    repo_name=$(extract_repo_name)
    
    if [[ -d $repo_name ]]; then
        rm -rf $repo_name
    fi
    
    git clone "$TARGET_REPO_URL"
    if [[ $? -ne 0 ]]; then
        echo "Error: Failed to clone repository"
        exit 1
    fi
}

# Create target directory if it doesn't exist
create_target_directory() {
    local repo_name
    repo_name=$(extract_repo_name)
    
    mkdir -p "$repo_name/$RELATIVE_PATH"
}

# Copy readme.html to the target repository
copy_readme_to_target_repo() {
    local repo_name
    repo_name=$(extract_repo_name)
    
    if [[ ! -f readme.html ]]; then
        echo "Error: readme.html not found"
        exit 1
    fi
    
    cp readme.html "$repo_name/$RELATIVE_PATH"
}

# Commit and push changes to the target repository
commit_and_push_changes() {
    local repo_name
    repo_name=$(extract_repo_name)
    
    cd "$repo_name"
    
    # Check for unstaged changes and stash them if necessary
    if [[ -n $(git status --porcelain) ]]; then
        git stash --include-untracked
    fi
    
    git checkout master
    git pull --rebase origin master
    
    git add "$RELATIVE_PATH/readme.html"
    git commit -m "$COMMIT_MESSAGE"
    git push origin master
    cd ..
}

# Main script execution
main() {
    # Change to the directory where the script is located
    cd "$(dirname "$0")"
    
    # Clone the target repository
    clone_target_repo
    
    # Create target directory if it doesn't exist
    create_target_directory
    
    # Copy readme.html to the target repository
    copy_readme_to_target_repo
    
    # Commit and push changes to the target repository
    commit_and_push_changes
    
    # Cleanup
    local repo_name
    repo_name=$(extract_repo_name)
    rm -rf "$repo_name"
    rm "readme.html"
}

# Execute the main function
main "$@"