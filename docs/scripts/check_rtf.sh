#!/bin/bash

echo "=== RTF Example Checker with Quarto Support ==="
echo "This script uses Quarto to render markdown examples and generate RTF files"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Directories
MD_DIR="$PROJECT_ROOT/docs/articles"
QMD_DIR="$PROJECT_ROOT/docs/articles/quarto_temp"
OUTPUT_DIR="$PROJECT_ROOT/docs/articles/output_temp"
RTF_DIR="$PROJECT_ROOT/docs/articles/rtf"
BASELINE_DIR="$PROJECT_ROOT/docs/articles/rtf_baseline"

# Check if Quarto is installed
check_quarto() {
    if ! command -v quarto &> /dev/null; then
        echo -e "${RED}Error: Quarto is not installed${NC}"
        echo "Please install Quarto from https://quarto.org"
        exit 1
    fi
    
    QUARTO_VERSION=$(quarto --version)
    echo -e "${BLUE}Using Quarto version: $QUARTO_VERSION${NC}"
    echo ""
}

# Function to convert markdown files to Quarto documents with RTF generation
prepare_quarto_documents() {
    echo "=== Step 1: Preparing Quarto documents from markdown ==="
    echo ""
    
    # Create temporary directories
    mkdir -p "$QMD_DIR"
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$RTF_DIR"
    
    local count=0
    
    # Process example markdown files
    for md_file in "$MD_DIR"/example-*.md "$MD_DIR"/quickstart.md; do
        if [[ -f "$md_file" ]]; then
            md_name=$(basename "$md_file" .md)
            qmd_output="$QMD_DIR/$md_name.qmd"
            
            echo "  Preparing: $md_name.qmd"
            
            # Create a Quarto document with proper YAML header and RTF generation
            {
                # Add Quarto YAML header
                cat <<EOF
---
title: "$md_name RTF Generation"
format:
  html:
    embed-resources: true
execute:
  echo: false
  warning: false
  error: false
jupyter: python3
---

EOF
                
                # Copy the markdown content
                cat "$md_file"
                
                # Add RTF generation code at the end
                cat <<EOF

\`\`\`{python}
#| echo: false
#| include: false

# Generate RTF file if doc object exists
import os
os.makedirs('$RTF_DIR', exist_ok=True)

if 'doc' in locals():
    rtf_path = f'$RTF_DIR/$md_name.rtf'
    doc.write_rtf(rtf_path)
    print(f'Generated RTF: {rtf_path}')
elif 'docs' in locals():
    # Handle multiple documents
    for i, d in enumerate(docs):
        rtf_path = f'$RTF_DIR/${md_name}_{i}.rtf'
        d.write_rtf(rtf_path)
        print(f'Generated RTF: {rtf_path}')
else:
    print('No RTF document object found to save')
\`\`\`
EOF
            } > "$qmd_output"
            
            if [[ -f "$qmd_output" ]]; then
                echo -e "    ${GREEN}✓${NC} Prepared Quarto document"
                ((count++))
            else
                echo -e "    ${RED}✗${NC} Failed to prepare Quarto document"
            fi
        fi
    done
    
    echo ""
    echo "Prepared $count Quarto documents"
    echo ""
}

# Function to render Quarto documents
render_quarto_documents() {
    echo "=== Step 2: Rendering Quarto documents ==="
    echo ""
    
    # Activate virtual environment for Python dependencies
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    local count=0
    local failed=0
    
    for qmd_file in "$QMD_DIR"/*.qmd; do
        if [[ -f "$qmd_file" ]]; then
            qmd_name=$(basename "$qmd_file" .qmd)
            echo "  Rendering: $qmd_name.qmd"
            
            # Render with Quarto
            cd "$QMD_DIR" || exit 1
            
            # Run quarto render with output directory
            output=$(quarto render "$qmd_name.qmd" --output-dir "$OUTPUT_DIR" 2>&1)
            exit_code=$?
            
            if [[ $exit_code -eq 0 ]]; then
                # Check if RTF was generated
                if ls "$RTF_DIR"/"$qmd_name"*.rtf 1> /dev/null 2>&1; then
                    echo -e "    ${GREEN}✓${NC} Rendered successfully with RTF output"
                    ((count++))
                else
                    echo -e "    ${YELLOW}⚠${NC} Rendered but no RTF generated"
                    echo "    Debug: Check $OUTPUT_DIR/$qmd_name.html for execution details"
                fi
            else
                echo -e "    ${RED}✗${NC} Failed to render (exit code: $exit_code)"
                echo "    Error output (first 5 lines):"
                echo "$output" | head -5
                ((failed++))
            fi
            
            cd - > /dev/null || exit 1
        fi
    done
    
    echo ""
    echo "Successfully rendered $count documents"
    if [[ $failed -gt 0 ]]; then
        echo -e "${YELLOW}Failed to render $failed documents${NC}"
    fi
    echo ""
}

# Function to download baseline RTF files from gh-pages
download_baseline() {
    echo "=== Step 3: Downloading baseline RTF files from gh-pages ==="
    echo ""
    
    # Create baseline directory
    mkdir -p "$BASELINE_DIR"
    
    # GitHub raw URL base
    GH_BASE="https://raw.githubusercontent.com/pharmaverse/rtflite/gh-pages/articles/rtf"
    
    # List of expected RTF files
    local count=0
    for rtf_file in "$RTF_DIR"/*.rtf; do
        if [[ -f "$rtf_file" ]]; then
            rtf_name=$(basename "$rtf_file")
            # For numbered files (e.g., example_0.rtf), try base name too
            base_name="${rtf_name%_[0-9].rtf}.rtf"
            
            echo "  Downloading: $rtf_name"
            
            # Try exact name first
            curl -s -o "$BASELINE_DIR/$rtf_name" "$GH_BASE/$rtf_name"
            
            # If not found, try base name
            if [[ ! -s "$BASELINE_DIR/$rtf_name" ]] && [[ "$base_name" != "$rtf_name" ]]; then
                curl -s -o "$BASELINE_DIR/$rtf_name" "$GH_BASE/$base_name"
            fi
            
            if [[ -f "$BASELINE_DIR/$rtf_name" ]] && [[ -s "$BASELINE_DIR/$rtf_name" ]]; then
                # Check if it's actually an RTF file
                if head -1 "$BASELINE_DIR/$rtf_name" | grep -q '^{\\rtf'; then
                    echo -e "    ${GREEN}✓${NC} Downloaded successfully"
                    ((count++))
                else
                    echo -e "    ${YELLOW}⚠${NC} File exists but may not be valid RTF"
                    rm "$BASELINE_DIR/$rtf_name"
                fi
            else
                echo -e "    ${YELLOW}⚠${NC} Not found in baseline"
                rm -f "$BASELINE_DIR/$rtf_name"
            fi
        fi
    done
    
    echo ""
    echo "Downloaded $count baseline RTF files"
    echo ""
}

# Function to compare RTF files
compare_rtf_files() {
    echo "=== Step 4: Comparing generated RTF with baseline ==="
    echo ""
    
    local identical=0
    local different=0
    local missing_baseline=0
    local missing_generated=0
    
    # Create directory for differences
    DIFF_DIR="$PROJECT_ROOT/rtf_differences"
    mkdir -p "$DIFF_DIR/baseline"
    mkdir -p "$DIFF_DIR/generated"
    
    # Create a detailed differences log
    DIFF_LOG="$DIFF_DIR/differences.log"
    > "$DIFF_LOG"
    
    echo "Detailed Differences Report" >> "$DIFF_LOG"
    echo "===========================" >> "$DIFF_LOG"
    echo "Generated: $(date)" >> "$DIFF_LOG"
    echo "" >> "$DIFF_LOG"
    
    # List to track files with differences
    local different_files=()
    
    # Compare each RTF file
    for rtf_file in "$RTF_DIR"/*.rtf; do
        if [[ -f "$rtf_file" ]]; then
            rtf_name=$(basename "$rtf_file")
            baseline_file="$BASELINE_DIR/$rtf_name"
            
            echo "  Comparing: $rtf_name"
            
            if [[ ! -f "$baseline_file" ]]; then
                echo -e "    ${YELLOW}⚠${NC} No baseline to compare"
                ((missing_baseline++))
                echo "File: $rtf_name - NO BASELINE" >> "$DIFF_LOG"
                # Keep the generated file if no baseline exists
                cp "$rtf_file" "$DIFF_DIR/generated/$rtf_name"
            else
                # Use diff to compare
                if diff -q "$rtf_file" "$baseline_file" > /dev/null 2>&1; then
                    echo -e "    ${GREEN}✓${NC} Identical to baseline"
                    ((identical++))
                else
                    echo -e "    ${RED}✗${NC} Different from baseline"
                    ((different++))
                    different_files+=("$rtf_name")
                    
                    # Copy both versions for comparison
                    cp "$baseline_file" "$DIFF_DIR/baseline/$rtf_name"
                    cp "$rtf_file" "$DIFF_DIR/generated/$rtf_name"
                    
                    # Log detailed differences
                    echo "File: $rtf_name" >> "$DIFF_LOG"
                    echo "----------------------------------------" >> "$DIFF_LOG"
                    
                    # Get file sizes
                    size_gen=$(wc -c < "$rtf_file")
                    size_base=$(wc -c < "$baseline_file")
                    echo "  Generated size: $size_gen bytes" >> "$DIFF_LOG"
                    echo "  Baseline size: $size_base bytes" >> "$DIFF_LOG"
                    echo "  Size difference: $((size_gen - size_base)) bytes" >> "$DIFF_LOG"
                    
                    # Show first differences
                    echo "  First differences:" >> "$DIFF_LOG"
                    diff -u "$baseline_file" "$rtf_file" | head -30 >> "$DIFF_LOG" 2>&1
                    echo "" >> "$DIFF_LOG"
                fi
            fi
        fi
    done
    
    echo ""
    echo "=== Summary ==="
    echo ""
    echo -e "  ${GREEN}Identical files:${NC} $identical"
    echo -e "  ${RED}Different files:${NC} $different"
    echo -e "  ${YELLOW}Missing baseline:${NC} $missing_baseline"
    echo -e "  ${YELLOW}Missing generated:${NC} $missing_generated"
    echo ""
    
    if [[ $different -gt 0 ]] || [[ $missing_baseline -gt 0 ]]; then
        echo "Files with differences saved to: $DIFF_DIR"
        echo "  - Baseline versions: $DIFF_DIR/baseline/"
        echo "  - Generated versions: $DIFF_DIR/generated/"
        echo "  - Differences log: $DIFF_LOG"
        echo ""
        
        if [[ ${#different_files[@]} -gt 0 ]]; then
            echo "Files with differences:"
            for file in "${different_files[@]}"; do
                echo "  - $file"
            done
            echo ""
        fi
        
        echo "To compare specific files:"
        echo "  diff -u $DIFF_DIR/baseline/<file>.rtf $DIFF_DIR/generated/<file>.rtf"
        echo ""
        echo "To open in Word for visual comparison:"
        echo "  open $DIFF_DIR/baseline/<file>.rtf"
        echo "  open $DIFF_DIR/generated/<file>.rtf"
    else
        # No differences, remove the diff directory
        rm -rf "$DIFF_DIR"
        echo -e "${GREEN}All files match baseline - no differences found${NC}"
    fi
    
    # Return appropriate exit code
    if [[ $different -eq 0 ]] && [[ $missing_generated -eq 0 ]]; then
        echo -e "${GREEN}✓ All checks passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some differences detected${NC}"
        return 1
    fi
}

# Function to clean up temporary files
cleanup() {
    echo ""
    echo "=== Cleanup ==="
    
    local response
    
    if [[ -d "$QMD_DIR" ]]; then
        read -p "Remove temporary Quarto files? (y/n) " -n 1 -r response
        echo ""
        if [[ $response =~ ^[Yy]$ ]]; then
            rm -rf "$QMD_DIR"
            echo "Temporary Quarto files removed"
        fi
    fi
    
    if [[ -d "$OUTPUT_DIR" ]]; then
        read -p "Remove HTML output files? (y/n) " -n 1 -r response
        echo ""
        if [[ $response =~ ^[Yy]$ ]]; then
            rm -rf "$OUTPUT_DIR"
            echo "HTML output files removed"
        fi
    fi
    
    if [[ -d "$BASELINE_DIR" ]]; then
        read -p "Remove all downloaded baseline files? (y/n) " -n 1 -r response
        echo ""
        if [[ $response =~ ^[Yy]$ ]]; then
            rm -rf "$BASELINE_DIR"
            echo "Baseline files removed"
        fi
    fi
    
    # Keep differences directory if it has content
    if [[ -d "$PROJECT_ROOT/rtf_differences" ]]; then
        echo ""
        echo -e "${YELLOW}Note:${NC} Differences directory preserved at: $PROJECT_ROOT/rtf_differences"
        echo "      This contains RTF files that differ from baseline for comparison"
        echo "      Remove manually when no longer needed: rm -rf $PROJECT_ROOT/rtf_differences"
    fi
}

# Main execution
main() {
    # Parse command line arguments
    SKIP_PREPARE=false
    SKIP_RENDER=false
    SKIP_DOWNLOAD=false
    CLEANUP_AUTO=false
    KEEP_TEMP=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-prepare)
                SKIP_PREPARE=true
                shift
                ;;
            --skip-render)
                SKIP_RENDER=true
                shift
                ;;
            --skip-download)
                SKIP_DOWNLOAD=true
                shift
                ;;
            --cleanup)
                CLEANUP_AUTO=true
                shift
                ;;
            --keep-temp)
                KEEP_TEMP=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "This script uses Quarto to render markdown documentation and generate RTF files,"
                echo "then compares them with baseline RTF files from the gh-pages branch."
                echo ""
                echo "Options:"
                echo "  --skip-prepare     Skip Quarto document preparation"
                echo "  --skip-render      Skip Quarto rendering step"
                echo "  --skip-download    Skip baseline download step"
                echo "  --cleanup          Automatically cleanup after comparison"
                echo "  --keep-temp        Keep temporary files (QMD and HTML outputs)"
                echo "  --help             Show this help message"
                echo ""
                echo "Requirements:"
                echo "  - Quarto must be installed (https://quarto.org)"
                echo "  - Python virtual environment at .venv/"
                echo "  - rtflite package installed in the virtual environment"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Check for Quarto
    check_quarto
    
    # Run steps
    if [[ "$SKIP_PREPARE" != true ]]; then
        prepare_quarto_documents
    fi
    
    if [[ "$SKIP_RENDER" != true ]]; then
        render_quarto_documents
    fi
    
    if [[ "$SKIP_DOWNLOAD" != true ]]; then
        download_baseline
    fi
    
    # Compare files
    compare_rtf_files
    RESULT=$?
    
    # Cleanup
    if [[ "$CLEANUP_AUTO" == true ]]; then
        rm -rf "$QMD_DIR" "$OUTPUT_DIR" "$BASELINE_DIR"
        echo "Automatic cleanup completed (temporary files removed)"
        if [[ -d "$PROJECT_ROOT/rtf_differences" ]]; then
            echo -e "${YELLOW}Note:${NC} Differences preserved at: $PROJECT_ROOT/rtf_differences"
        fi
    elif [[ "$KEEP_TEMP" != true ]]; then
        cleanup
    else
        echo ""
        echo "Temporary files kept in:"
        echo "  Quarto files: $QMD_DIR"
        echo "  HTML outputs: $OUTPUT_DIR"
        echo "  Baseline files: $BASELINE_DIR"
        if [[ -d "$PROJECT_ROOT/rtf_differences" ]]; then
            echo "  Differences: $PROJECT_ROOT/rtf_differences"
        fi
    fi
    
    exit $RESULT
}

# Run main function
main "$@"