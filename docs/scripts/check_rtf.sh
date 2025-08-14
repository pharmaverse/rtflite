#!/bin/bash

# Simplified RTF Checker Script
# Uses markdown-exec to run Python code directly from markdown files
# Dynamically fetches RTF file list from gh-pages branch

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Configuration
TEMP_DIR="$PROJECT_ROOT/docs_temp"
MD_DIR="$PROJECT_ROOT/docs/articles"
RTF_DIR="$TEMP_DIR/rtf_generated"
BASELINE_DIR="$TEMP_DIR/rtf_baseline"
DIFF_DIR="$TEMP_DIR/rtf_differences"

# GitHub configuration
GH_REPO="pharmaverse/rtflite"
GH_BRANCH="gh-pages"
GH_PATH="articles/rtf"

# Clean up function
cleanup() {
    if [[ "$KEEP_TEMP" != "true" ]]; then
        echo "Cleaning up temporary files..."
        rm -rf "$TEMP_DIR"
    fi
}

# Set up trap for cleanup on exit
trap cleanup EXIT

# Initialize directories
init_directories() {
    echo "Initializing directories..."
    rm -rf "$TEMP_DIR"
    mkdir -p "$RTF_DIR"
    mkdir -p "$BASELINE_DIR"
    mkdir -p "$DIFF_DIR/baseline"
    mkdir -p "$DIFF_DIR/generated"
}

# Dynamically get list of RTF files from gh-pages branch
get_baseline_rtf_list() {
    echo "Fetching RTF file list from gh-pages branch..." >&2
    
    # Use GitHub API to get file list
    local api_url="https://api.github.com/repos/$GH_REPO/contents/$GH_PATH?ref=$GH_BRANCH"
    
    # Fetch and parse JSON response for .rtf files
    local rtf_files=$(curl -s "$api_url" | \
        python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get('name', '').endswith('.rtf'):
                print(item['name'])
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
")
    
    if [[ -z "$rtf_files" ]]; then
        echo -e "${RED}Error: No RTF files found via GitHub API${NC}" >&2
        return 1
    fi
    
    echo "$rtf_files"
}

# Download baseline RTF files
download_baseline() {
    echo -e "\n${BLUE}=== Downloading Baseline RTF Files ===${NC}"
    
    local rtf_list=$(get_baseline_rtf_list)
    if [[ -z "$rtf_list" ]]; then
        return 1
    fi
    
    local count=0
    local base_url="https://raw.githubusercontent.com/$GH_REPO/$GH_BRANCH/$GH_PATH"
    
    while IFS= read -r rtf_file; do
        if curl -s -o "$BASELINE_DIR/$rtf_file" "$base_url/$rtf_file"; then
            # Verify it's a valid RTF file
            if head -1 "$BASELINE_DIR/$rtf_file" | grep -q '^{\\rtf'; then
                echo -e "  Downloading $rtf_file: ${GREEN}[OK]${NC}"
                ((count++))
            else
                echo -e "  Downloading $rtf_file: ${YELLOW}[INVALID]${NC}"
                rm -f "$BASELINE_DIR/$rtf_file"
            fi
        else
            echo -e "  Downloading $rtf_file: ${RED}[FAILED]${NC}"
        fi
    done <<< "$rtf_list"
    
    echo -e "Downloaded $count baseline RTF files\n"
}

# Generate RTF files using markdown-exec
generate_rtf_files() {
    echo -e "${BLUE}=== Generating RTF Files from Markdown ===${NC}"
    
    local count=0
    local failed=0
    
    # Process each markdown file
    for md_file in "$MD_DIR"/*.md; do
        if [[ ! -f "$md_file" ]]; then
            continue
        fi
        
        # Check if file contains executable Python code
        if ! grep -q 'exec="on"' "$md_file"; then
            continue
        fi
        
        local md_name=$(basename "$md_file" .md)
        echo "  Processing: $md_name.md"
        
        # Create a temporary Python script that will be executed by markdown-exec
        # This script will capture RTF documents and save them
        cat > "$TEMP_DIR/rtf_generator.py" << 'EOF'
import sys
import os
from pathlib import Path

# Set up paths
rtf_dir = sys.argv[1]
md_name = sys.argv[2]

# Capture globals after markdown execution
def save_rtf_documents(globals_dict):
    """Find and save all RTFDocument objects"""
    rtf_docs = []
    for name, obj in globals_dict.items():
        if hasattr(obj, 'write_rtf') and hasattr(obj, 'rtf_encode'):
            rtf_docs.append((name, obj))
    
    if rtf_docs:
        for doc_name, doc in rtf_docs:
            if doc_name == 'doc':
                rtf_path = os.path.join(rtf_dir, f'{md_name}.rtf')
            else:
                rtf_path = os.path.join(rtf_dir, f'{md_name}_{doc_name}.rtf')
            
            try:
                doc.write_rtf(rtf_path)
                print(f'    Generated: {os.path.basename(rtf_path)}')
            except Exception as e:
                print(f'    Error: {e}')
    else:
        print(f'    No RTF documents found in {md_name}.md')

EOF
        
        # Use markdown-exec to execute the Python code blocks
        # and then save the RTF documents
        python3 -c "
import sys
import os
import re
from pathlib import Path
from markdown_exec import formatter, validator

# Read the markdown file
md_path = '$md_file'
with open(md_path, 'r') as f:
    content = f.read()

# Extract intended file names from write_rtf calls
write_rtf_files = []
for match in re.finditer(r'(\w+)\.write_rtf\([\"\'](.*?)[\"\']', content):
    var_name = match.group(1)
    filename = match.group(2)
    write_rtf_files.append((var_name, filename))

# Process each code block individually to handle variable reuse
rtf_dir = '$RTF_DIR'
md_name = '$md_name'
generated_files = []

# Track which RTF files we've generated from each code block
rtf_file_index = 0

# Extract and execute Python code blocks with exec='on' individually
for match in re.finditer(r'\`\`\`python.*?exec=\"on\".*?\n(.*?)\`\`\`', content, re.DOTALL):
    code_block_header = match.group(0).split('\n')[0]  # Get the first line with parameters
    code = match.group(1)
    
    # Extract workdir if specified
    workdir = None
    if 'workdir=' in code_block_header:
        workdir_match = re.search(r'workdir=\"([^\"]+)\"', code_block_header)
        if workdir_match:
            workdir = workdir_match.group(1)
    
    # Check if this code block has a write_rtf call or creates images
    has_write_rtf = '.write_rtf(' in code and not all(line.strip().startswith('#') for line in code.split('\n') if '.write_rtf(' in line)
    creates_images = 'plt.savefig(' in code or 'matplotlib' in code
    
    if not has_write_rtf and not creates_images:
        continue
        
    # Skip write_rtf and converter.convert calls in execution
    lines = []
    for line in code.split('\n'):
        if '.write_rtf(' in line and not line.strip().startswith('#'):
            lines.append('# ' + line + '  # Skipped for separate execution')
        elif 'converter.convert(' in line and not line.strip().startswith('#'):
            lines.append('# ' + line + '  # Skipped')
        else:
            lines.append(line)
    modified_code = '\n'.join(lines)
    
    # Execute this code block
    globals_dict = {}
    try:
        # Create image directories and set up working directory for figure examples
        import os
        # Ensure images directory exists where the code expects it
        images_dir = os.path.join('$PROJECT_ROOT', 'docs', 'articles', 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # First execute all previous code blocks for context
        prev_blocks = []
        for prev_match in re.finditer(r'\`\`\`python.*?exec=\"on\".*?\n(.*?)\`\`\`', content[:match.start()], re.DOTALL):
            prev_code = prev_match.group(1)
            prev_lines = []
            for line in prev_code.split('\n'):
                if '.write_rtf(' in line and not line.strip().startswith('#'):
                    prev_lines.append('# ' + line + '  # Skipped')
                elif 'converter.convert(' in line and not line.strip().startswith('#'):
                    prev_lines.append('# ' + line + '  # Skipped') 
                else:
                    prev_lines.append(line)
            prev_blocks.append('\n'.join(prev_lines))
        
        # Execute previous blocks for context
        if prev_blocks:
            context_code = '\n\n'.join(prev_blocks)
            exec(context_code, globals_dict)
        
        # Change to working directory if specified
        original_cwd = os.getcwd()
        if workdir:
            # Resolve workdir relative to project root
            target_dir = os.path.join('$PROJECT_ROOT', workdir)
            os.makedirs(target_dir, exist_ok=True)
            
            # For figure examples, ensure the images directory exists
            # where the code expects it relative to the working directory
            if 'rtf/' in workdir:
                # When in rtf/ directory, ../images/ should exist
                images_relative_dir = os.path.join(target_dir, '..', 'images')
                os.makedirs(images_relative_dir, exist_ok=True)
                
                # Copy required images from main project to temp structure
                import shutil
                source_images_dir = os.path.join('$PROJECT_ROOT', 'docs', 'articles', 'images')
                if os.path.exists(source_images_dir):
                    for img_file in ['age-histogram-treatment-0.png', 'age-histogram-treatment-1.png', 'age-histogram-treatment-2.png']:
                        source_img = os.path.join(source_images_dir, img_file)
                        target_img = os.path.join(images_relative_dir, img_file)
                        if os.path.exists(source_img) and not os.path.exists(target_img):
                            shutil.copy2(source_img, target_img)
            elif 'images/' in workdir:
                # When in images/ directory, make sure it exists
                os.makedirs(target_dir, exist_ok=True)
            
            os.chdir(target_dir)
        
        try:
            # Execute current block
            exec(modified_code, globals_dict)
        finally:
            # Always restore original working directory
            os.chdir(original_cwd)
        
        # Find RTF documents and save them
        rtf_docs = []
        for name, obj in globals_dict.items():
            if hasattr(obj, 'write_rtf') and hasattr(obj, 'rtf_encode'):
                rtf_docs.append((name, obj))
        
        # Save each RTF document with the correct filename
        for doc_name, doc in rtf_docs:
            # Find the corresponding write_rtf filename for this document
            rtf_filename = None
            
            # Look for matching write_rtf call in original code
            for write_match in re.finditer(r'(\w+)\.write_rtf\([\"\'](.*?)[\"\']', code):
                if write_match.group(1) == doc_name:
                    rtf_filename = write_match.group(2)
                    break
            
            # Only generate RTF if we found an explicit write_rtf call
            # This avoids duplicate generation with fallback names
            if rtf_filename:
                rtf_path = os.path.join(rtf_dir, rtf_filename)
                try:
                    doc.write_rtf(rtf_path)
                    print(f'    Generated: {rtf_filename}')
                    generated_files.append(rtf_filename)
                except Exception as e:
                    print(f'    Error generating {rtf_filename}: {e}')
            else:
                print(f'    Skipping {doc_name}: no explicit write_rtf call found')
        
    except Exception as e:
        print(f'    Execution error in code block: {e}')
"
        
        if [[ $? -eq 0 ]]; then
            ((count++))
        else
            ((failed++))
        fi
    done
    
    echo -e "\nGenerated RTF files from $count markdown files"
    if [[ $failed -gt 0 ]]; then
        echo -e "${YELLOW}Failed to process $failed files${NC}"
    fi
}

# Compare RTF files
compare_rtf_files() {
    echo -e "\n${BLUE}=== Comparing RTF Files ===${NC}"
    
    local identical=0
    local different=0
    local missing_baseline=0
    local missing_generated=0
    
    
    # Compare each generated file with corresponding baseline
    for gen_file in "$RTF_DIR"/*.rtf; do
        if [[ ! -f "$gen_file" ]]; then
            continue
        fi
        
        gen_name=$(basename "$gen_file")
        baseline_file="$BASELINE_DIR/$gen_name"
        
        if [[ ! -f "$baseline_file" ]]; then
            echo -e "  $gen_name: ${YELLOW}[NO BASELINE]${NC}"
            ((missing_baseline++))
            cp "$gen_file" "$DIFF_DIR/$gen_name"
        elif diff -q "$gen_file" "$baseline_file" > /dev/null 2>&1; then
            echo -e "  $gen_name: ${GREEN}[IDENTICAL]${NC}"
            ((identical++))
        else
            echo -e "  $gen_name: ${RED}[DIFFERENT]${NC}"
            ((different++))
            cp "$gen_file" "$DIFF_DIR/generated/$gen_name"
            cp "$baseline_file" "$DIFF_DIR/baseline/$gen_name"
        fi
    done
    
    # Check for baseline files that don't have corresponding generated files
    for baseline_file in "$BASELINE_DIR"/*.rtf; do
        if [[ ! -f "$baseline_file" ]]; then
            continue
        fi
        
        baseline_name=$(basename "$baseline_file")
        gen_file="$RTF_DIR/$baseline_name"
        
        if [[ ! -f "$gen_file" ]]; then
            echo -e "  $baseline_name: ${RED}[MISSING GENERATED]${NC}"
            ((missing_generated++))
            cp "$baseline_file" "$DIFF_DIR/baseline/$baseline_name"
        fi
    done
    
    # Summary
    echo -e "\n${BLUE}=== Summary ===${NC}"
    echo "  Identical: $identical"
    echo "  Different: $different"
    echo "  Missing baseline: $missing_baseline"
    echo "  Missing generated: $missing_generated"
    
    if [[ $different -gt 0 ]] || [[ $missing_baseline -gt 0 ]] || [[ $missing_generated -gt 0 ]]; then
        echo -e "\n${YELLOW}Differences saved to: $DIFF_DIR${NC}"
        return 1
    else
        echo -e "\n${GREEN}All files match baseline!${NC}"
        return 0
    fi
}

# Main execution
main() {
    echo -e "${BLUE}RTF Document Comparison Tool (Simplified)${NC}"
    echo "=========================================="
    
    # Parse arguments
    KEEP_TEMP=false
    while [[ $# -gt 0 ]]; do
        case $1 in
            --keep-temp)
                KEEP_TEMP=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --keep-temp    Keep temporary files after execution"
                echo "  --help         Show this help message"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Initialize
    init_directories
    
    # Download baseline
    download_baseline || exit 1
    
    # Generate RTF files
    generate_rtf_files
    
    # Compare files
    compare_rtf_files
    exit_code=$?
    
    if [[ "$KEEP_TEMP" == "true" ]]; then
        echo -e "\nTemporary files kept in: $TEMP_DIR"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"