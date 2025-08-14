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

# All temporary files will be stored in docs_temp
TEMP_BASE="$PROJECT_ROOT/docs_temp"

# Directories
MD_DIR="$PROJECT_ROOT/docs/articles"
QMD_DIR="$TEMP_BASE/qmd"
OUTPUT_DIR="$TEMP_BASE/html"
PY_DIR="$TEMP_BASE/py"
RTF_DIR="$TEMP_BASE/rtf_generated"
BASELINE_DIR="$TEMP_BASE/rtf_baseline"
DIFF_DIR="$TEMP_BASE/rtf_differences"

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

# Function to prepare Quarto documents from markdown files
prepare_quarto_documents() {
    echo "=== Step 1: Preparing Quarto documents from markdown ==="
    echo ""
    
    # Create temp directories
    mkdir -p "$QMD_DIR"
    mkdir -p "$OUTPUT_DIR"
    mkdir -p "$RTF_DIR"
    
    local count=0
    
    # Process markdown files that contain executable Python code
    for md_file in "$MD_DIR"/*.md; do
        if [[ -f "$md_file" ]] && grep -q 'exec="on"' "$md_file"; then
            md_name=$(basename "$md_file" .md)
            qmd_output="$QMD_DIR/$md_name.qmd"
            
            echo "  Preparing: $md_name.qmd"
            
            # Create a Quarto document with proper YAML header
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
                
                # Add RTF generation code at the end to save in docs_temp
                cat <<EOF

\`\`\`{python}
#| echo: false
#| include: false

# Generate RTF file if doc object exists
import os

# Find all RTFDocument objects that might have been created
rtf_docs = []
for name, obj in list(locals().items()):
    if hasattr(obj, 'write_rtf') and hasattr(obj, 'rtf_encode'):
        rtf_docs.append((name, obj))

if rtf_docs:
    for doc_name, doc in rtf_docs:
        # Generate a unique name based on the document variable
        if doc_name == 'doc':
            rtf_path = f'$RTF_DIR/$md_name.rtf'
        else:
            # Handle multiple documents with unique names
            rtf_path = f'$RTF_DIR/${md_name}_{doc_name}.rtf'
        
        doc.write_rtf(rtf_path)
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

# Function to extract Python code from markdown (alternative to Quarto)
extract_python_from_markdown() {
    echo "=== Step 1 (Alternative): Extracting Python code from markdown ==="
    echo ""
    
    # Create temp directories
    mkdir -p "$PY_DIR"
    mkdir -p "$RTF_DIR"
    
    local count=0
    
    # Process markdown files with executable Python code
    for md_file in "$MD_DIR"/*.md; do
        if [[ -f "$md_file" ]] && grep -q 'exec="on"' "$md_file"; then
            md_name=$(basename "$md_file" .md)
            py_output="$PY_DIR/$md_name.py"
            
            echo "  Processing: $md_name.md"
            
            # Extract Python code blocks and create executable script
            {
                echo "#!/usr/bin/env python"
                echo "# Auto-generated from $md_name.md"
                echo ""
                
                # Extract Python code blocks with exec="on" or source="above"
                awk '
                    /^```python.*exec="on"/ || /^```python.*source="above"/ { 
                        in_block = 1
                        next
                    }
                    /^```$/ && in_block { 
                        in_block = 0
                        print ""
                        next
                    }
                    in_block { 
                        print $0
                    }
                ' "$md_file"
                
                # Add RTF generation code
                cat <<EOF

# Generate RTF files
import os
os.makedirs('$RTF_DIR', exist_ok=True)

# Find all RTFDocument objects
rtf_docs = []
for name, obj in list(locals().items()):
    if hasattr(obj, 'write_rtf') and hasattr(obj, 'rtf_encode'):
        rtf_docs.append((name, obj))

if rtf_docs:
    for doc_name, doc in rtf_docs:
        if doc_name == 'doc':
            rtf_path = f'$RTF_DIR/$md_name.rtf'
        else:
            rtf_path = f'$RTF_DIR/${md_name}_{doc_name}.rtf'
        doc.write_rtf(rtf_path)
        print(f'Generated: {rtf_path}')
else:
    print('No RTF document found in $md_name.py')
EOF
            } > "$py_output"
            
            chmod +x "$py_output"
            
            if [[ -s "$py_output" ]]; then
                echo -e "    ${GREEN}✓${NC} Extracted Python code"
                ((count++))
            else
                echo -e "    ${YELLOW}⚠${NC} No executable Python code found"
                rm -f "$py_output"
            fi
        fi
    done
    
    echo ""
    echo "Extracted Python from $count markdown files"
    echo ""
}

# Function to render Quarto documents
render_quarto_documents() {
    echo "=== Step 2: Rendering Quarto documents ==="
    echo ""
    
    # Activate virtual environment
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    local count=0
    local failed=0
    
    for qmd_file in "$QMD_DIR"/*.qmd; do
        if [[ -f "$qmd_file" ]]; then
            qmd_name=$(basename "$qmd_file" .qmd)
            echo "  Rendering: $qmd_name.qmd"
            
            cd "$QMD_DIR" || exit 1
            
            # Run quarto render
            output=$(quarto render "$qmd_name.qmd" --output-dir "$OUTPUT_DIR" 2>&1)
            exit_code=$?
            
            if [[ $exit_code -eq 0 ]]; then
                # Check if RTF was generated
                if ls "$RTF_DIR"/"$qmd_name"*.rtf 1> /dev/null 2>&1; then
                    echo -e "    ${GREEN}✓${NC} Rendered successfully with RTF output"
                    ((count++))
                else
                    echo -e "    ${YELLOW}⚠${NC} Rendered but no RTF generated"
                fi
            else
                echo -e "    ${RED}✗${NC} Failed to render (exit code: $exit_code)"
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

# Function to generate RTF files from Python scripts
generate_rtf_files() {
    echo "=== Step 2 (Alternative): Generating RTF files from Python scripts ==="
    echo ""
    
    # Activate virtual environment
    source "$PROJECT_ROOT/.venv/bin/activate"
    
    local count=0
    local failed=0
    
    for py_file in "$PY_DIR"/*.py; do
        if [[ -f "$py_file" ]]; then
            py_name=$(basename "$py_file" .py)
            echo "  Running: $py_name.py"
            
            # Run Python script
            cd "$PROJECT_ROOT" || exit 1
            output=$(python "$py_file" 2>&1)
            exit_code=$?
            
            if [[ $exit_code -eq 0 ]]; then
                # Check if RTF was created
                if ls "$RTF_DIR"/"$py_name"*.rtf 1> /dev/null 2>&1; then
                    echo -e "    ${GREEN}✓${NC} Generated successfully"
                    ((count++))
                else
                    echo -e "    ${YELLOW}⚠${NC} Script ran but no RTF created"
                fi
            else
                echo -e "    ${RED}✗${NC} Failed to generate (exit code: $exit_code)"
                echo "    First error lines:"
                echo "$output" | head -5
                ((failed++))
            fi
            
            cd - > /dev/null || exit 1
        fi
    done
    
    echo ""
    echo "Generated $count RTF files"
    if [[ $failed -gt 0 ]]; then
        echo -e "${YELLOW}Failed to generate $failed files${NC}"
    fi
    echo ""
}

# Function to download baseline RTF files
download_baseline() {
    echo "=== Step 3: Downloading baseline RTF files from gh-pages ==="
    echo ""
    
    mkdir -p "$BASELINE_DIR"
    
    # GitHub raw URL base
    GH_BASE="https://raw.githubusercontent.com/pharmaverse/rtflite/gh-pages/articles/rtf"
    
    # Get list of expected RTF files from generated files
    local count=0
    
    # First, get a list of all known RTF files from gh-pages
    # This list should include all possible RTF outputs
    local known_rtf_files=(
        "advanced-group-by-comprehensive.rtf"
        "advanced-group-by-group-newpage.rtf"
        "advanced-group-by-multipage.rtf"
        "advanced-group-by-single.rtf"
        "advanced-group-by-subline.rtf"
        "example-ae-summary.rtf"
        "example-baseline-char.rtf"
        "example-efficacy.rtf"
        "example-figure-age.rtf"
        "example-figure-multipage.rtf"
        "format-page-all-pages.rtf"
        "format-page-custom.rtf"
        "format-page-default.rtf"
        "format-page-footnote-first.rtf"
        "format-page-title-first.rtf"
        "intro-ae1.rtf"
        "intro-ae10.rtf"
        "intro-ae11.rtf"
        "intro-ae12.rtf"
        "intro-ae2.rtf"
        "intro-ae3.rtf"
        "intro-ae4.rtf"
        "intro-ae5.rtf"
        "intro-ae6.rtf"
        "intro-ae7.rtf"
        "intro-ae8.rtf"
        "intro-ae8b.rtf"
        "row-border-styles.rtf"
        "row-column-widths.rtf"
        "text-color.rtf"
        "text-convert.rtf"
        "text-font-size-alignment.rtf"
        "text-format-styles.rtf"
        "text-indentation.rtf"
    )
    
    for rtf_name in "${known_rtf_files[@]}"; do
        echo "  Downloading: $rtf_name"
        curl -s -o "$BASELINE_DIR/$rtf_name" "$GH_BASE/$rtf_name"
        
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
    local identical_files=()
    local missing_in_generated=()
    
    # Function to map generated file names to baseline names
    get_baseline_name() {
        local gen_name="$1"
        case "$gen_name" in
            "advanced-group-by_doc_comprehensive.rtf") echo "advanced-group-by-comprehensive.rtf" ;;
            "advanced-group-by_doc_multipage.rtf") echo "advanced-group-by-multipage.rtf" ;;
            "advanced-group-by_doc_single.rtf") echo "advanced-group-by-single.rtf" ;;
            "advanced-group-by_doc_subline.rtf") echo "advanced-group-by-subline.rtf" ;;
            "advanced-group-by_doc_treatment_separated.rtf") echo "advanced-group-by-group-newpage.rtf" ;;
            "example-ae.rtf") echo "example-ae-summary.rtf" ;;
            "example-baseline.rtf") echo "example-baseline-char.rtf" ;;
            "example-efficacy.rtf") echo "example-efficacy.rtf" ;;
            "example-figure_doc_age.rtf") echo "example-figure-age.rtf" ;;
            "example-figure_doc_multipage.rtf") echo "example-figure-multipage.rtf" ;;
            "format-page_doc_default.rtf") echo "format-page-default.rtf" ;;
            "format-page_doc_title_first.rtf") echo "format-page-title-first.rtf" ;;
            "format-page_doc_footnote_first.rtf") echo "format-page-footnote-first.rtf" ;;
            "format-page_doc_all_pages.rtf") echo "format-page-all-pages.rtf" ;;
            "format-page_doc_custom.rtf") echo "format-page-custom.rtf" ;;
            "format-row_doc_borders.rtf") echo "row-border-styles.rtf" ;;
            "format-row_doc_widths.rtf") echo "row-column-widths.rtf" ;;
            "format-text_doc_colors.rtf") echo "text-color.rtf" ;;
            "format-text_doc_converted.rtf") echo "text-convert.rtf" ;;
            "format-text_doc_font_align.rtf") echo "text-font-size-alignment.rtf" ;;
            "format-text_doc_formats.rtf") echo "text-format-styles.rtf" ;;
            "format-text_doc_indent.rtf") echo "text-indentation.rtf" ;;
            "quickstart.rtf") echo "intro-ae1.rtf" ;;
            "quickstart_doc_converted.rtf") echo "intro-ae8.rtf" ;;
            *) echo "$gen_name" ;;  # Return original name if no mapping
        esac
    }
    
    # Compare each generated RTF file with its baseline
    for rtf_file in "$RTF_DIR"/*.rtf; do
        if [[ -f "$rtf_file" ]]; then
            rtf_name=$(basename "$rtf_file")
            
            # Get the baseline name from mapping
            baseline_name=$(get_baseline_name "$rtf_name")
            baseline_file="$BASELINE_DIR/$baseline_name"
            
            echo "  Comparing: $rtf_name -> $baseline_name"
            
            if [[ ! -f "$baseline_file" ]]; then
                echo -e "    ${YELLOW}[!]${NC} No baseline to compare"
                ((missing_baseline++))
                echo "File: $rtf_name - NO BASELINE" >> "$DIFF_LOG"
                # Keep the generated file if no baseline exists
                cp "$rtf_file" "$DIFF_DIR/generated/$rtf_name"
                different_files+=("$rtf_name (no baseline)")
            else
                # Use diff to compare
                if diff -q "$rtf_file" "$baseline_file" > /dev/null 2>&1; then
                    echo -e "    ${GREEN}[OK]${NC} Identical to baseline"
                    ((identical++))
                    identical_files+=("$rtf_name -> $baseline_name")
                    # Remove identical baseline file
                    rm -f "$baseline_file"
                else
                    echo -e "    ${RED}[X]${NC} Different from baseline"
                    ((different++))
                    different_files+=("$rtf_name -> $baseline_name")
                    
                    # Copy both versions for comparison
                    cp "$baseline_file" "$DIFF_DIR/baseline/$baseline_name"
                    cp "$rtf_file" "$DIFF_DIR/generated/$rtf_name"
                    
                    # Get file sizes
                    size_gen=$(wc -c < "$rtf_file")
                    size_base=$(wc -c < "$baseline_file")
                    size_diff=$((size_gen - size_base))
                    
                    # Show difference details in terminal
                    echo -e "      ${BLUE}Size:${NC} Generated: $size_gen bytes | Baseline: $size_base bytes | Diff: $size_diff bytes"
                    
                    # Log detailed differences
                    echo "File: $rtf_name → $baseline_name" >> "$DIFF_LOG"
                    echo "----------------------------------------" >> "$DIFF_LOG"
                    echo "  Generated size: $size_gen bytes" >> "$DIFF_LOG"
                    echo "  Baseline size: $size_base bytes" >> "$DIFF_LOG"
                    echo "  Size difference: $size_diff bytes" >> "$DIFF_LOG"
                    
                    # Show first lines of differences in terminal
                    echo "  First differences:" >> "$DIFF_LOG"
                    diff_output=$(diff -u "$baseline_file" "$rtf_file" 2>&1 | head -20)
                    echo "$diff_output" >> "$DIFF_LOG"
                    echo "" >> "$DIFF_LOG"
                fi
            fi
        fi
    done
    
    # Check for baseline files that weren't compared (missing in generated)
    for baseline_file in "$BASELINE_DIR"/*.rtf; do
        if [[ -f "$baseline_file" ]]; then
            baseline_name=$(basename "$baseline_file")
            # If baseline file still exists, it wasn't matched/compared
            if [[ ! " ${identical_files[@]} " =~ " ${baseline_name} " ]]; then
                echo -e "  ${YELLOW}[!]${NC} Missing in generated: $baseline_name"
                ((missing_generated++))
                missing_in_generated+=("$baseline_name")
            fi
        fi
    done
    
    echo ""
    echo "======================================================================"
    echo "                        RTF COMPARISON SUMMARY                       "
    echo "======================================================================"
    echo ""
    echo -e "  ${GREEN}[OK] Identical files:${NC} $identical"
    echo -e "  ${RED}[X] Different files:${NC} $different"
    echo -e "  ${YELLOW}[!] Missing baseline:${NC} $missing_baseline"
    echo -e "  ${YELLOW}[!] Missing generated:${NC} $missing_generated"
    echo ""
    
    # Show detailed lists
    if [[ ${#identical_files[@]} -gt 0 ]]; then
        echo "----------------------------------------------------------------------"
        echo -e "${GREEN}IDENTICAL FILES (removed from baseline):${NC}"
        for file in "${identical_files[@]}"; do
            echo "  [OK] $file"
        done
        echo ""
    fi
    
    if [[ ${#different_files[@]} -gt 0 ]]; then
        echo "----------------------------------------------------------------------"
        echo -e "${RED}FILES WITH DIFFERENCES:${NC}"
        for file in "${different_files[@]}"; do
            echo "  [X] $file"
        done
        echo ""
    fi
    
    if [[ ${#missing_in_generated[@]} -gt 0 ]]; then
        echo "----------------------------------------------------------------------"
        echo -e "${YELLOW}MISSING IN GENERATED OUTPUT:${NC}"
        for file in "${missing_in_generated[@]}"; do
            echo "  [!] $file"
        done
        echo ""
    fi
    
    if [[ $different -gt 0 ]] || [[ $missing_baseline -gt 0 ]] || [[ $missing_generated -gt 0 ]]; then
        echo "----------------------------------------------------------------------"
        echo "DIFFERENCE FILES SAVED TO:"
        echo "  $DIFF_DIR"
        echo "     |-- baseline/     (original RTF files)"
        echo "     |-- generated/    (new RTF files)"
        echo "     +-- differences.log (detailed diff output)"
        echo ""
        echo "TO COMPARE FILES:"
        echo "  diff -u $DIFF_DIR/baseline/<file>.rtf $DIFF_DIR/generated/<file>.rtf"
        echo ""
        echo "TO VIEW IN WORD:"
        echo "  open $DIFF_DIR/baseline/<file>.rtf"
        echo "  open $DIFF_DIR/generated/<file>.rtf"
        echo ""
    else
        # No differences, remove empty diff directories
        rmdir "$DIFF_DIR/baseline" "$DIFF_DIR/generated" 2>/dev/null
        rm -f "$DIFF_LOG"
        echo "----------------------------------------------------------------------"
        echo -e "${GREEN}[SUCCESS] ALL FILES MATCH BASELINE - NO DIFFERENCES FOUND${NC}"
        echo ""
    fi
    
    # Return appropriate exit code
    if [[ $different -eq 0 ]] && [[ $missing_generated -eq 0 ]]; then
        echo -e "${GREEN}[OK] All checks passed!${NC}"
        return 0
    else
        echo -e "${RED}[FAIL] Some differences detected${NC}"
        return 1
    fi
}

# Function to clean up temporary files
cleanup() {
    echo ""
    echo "=== Cleanup ==="
    
    local response
    
    if [[ -d "$TEMP_BASE" ]]; then
        # Check if there are differences to preserve
        if [[ -d "$DIFF_DIR" ]] && [[ -n "$(ls -A "$DIFF_DIR")" ]]; then
            echo -e "${YELLOW}Note:${NC} Differences found and preserved in: $DIFF_DIR"
            read -p "Remove all other temporary files? (y/n) " -n 1 -r response
            echo ""
            if [[ $response =~ ^[Yy]$ ]]; then
                # Remove everything except differences
                rm -rf "$QMD_DIR" "$OUTPUT_DIR" "$PY_DIR" "$RTF_DIR" "$BASELINE_DIR"
                echo "Temporary files removed (differences preserved)"
            fi
        else
            read -p "Remove all temporary files? (y/n) " -n 1 -r response
            echo ""
            if [[ $response =~ ^[Yy]$ ]]; then
                rm -rf "$TEMP_BASE"
                echo "All temporary files removed"
            fi
        fi
    fi
}

# Main execution
main() {
    # Parse command line arguments
    USE_PYTHON=false
    SKIP_PREPARE=false
    SKIP_RENDER=false
    SKIP_DOWNLOAD=false
    CLEANUP_AUTO=false
    KEEP_TEMP=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --use-python)
                USE_PYTHON=true
                shift
                ;;
            --skip-prepare)
                SKIP_PREPARE=true
                shift
                ;;
            --skip-render|--skip-generation)
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
                echo "This script processes markdown files from docs/articles to generate and compare RTF outputs."
                echo "All temporary files are stored in docs_temp/ folder."
                echo ""
                echo "Options:"
                echo "  --use-python       Use Python extraction instead of Quarto rendering"
                echo "  --skip-prepare     Skip document preparation step"
                echo "  --skip-render      Skip rendering/generation step"
                echo "  --skip-download    Skip baseline download step"
                echo "  --cleanup          Automatically cleanup after comparison"
                echo "  --keep-temp        Keep all temporary files"
                echo "  --help             Show this help message"
                echo ""
                echo "Requirements:"
                echo "  - Quarto (optional, can use --use-python instead)"
                echo "  - Python virtual environment at .venv/"
                echo "  - rtflite package installed in the virtual environment"
                echo ""
                echo "Source: Markdown files in docs/articles/"
                echo "Output: All files in docs_temp/"
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Create temp base directory
    mkdir -p "$TEMP_BASE"
    echo "All temporary files will be stored in: $TEMP_BASE"
    echo ""
    
    # Check for Quarto if not using Python
    if [[ "$USE_PYTHON" != true ]]; then
        check_quarto
    fi
    
    # Run steps based on mode
    if [[ "$USE_PYTHON" == true ]]; then
        # Python mode
        if [[ "$SKIP_PREPARE" != true ]]; then
            extract_python_from_markdown
        fi
        
        if [[ "$SKIP_RENDER" != true ]]; then
            generate_rtf_files
        fi
    else
        # Quarto mode
        if [[ "$SKIP_PREPARE" != true ]]; then
            prepare_quarto_documents
        fi
        
        if [[ "$SKIP_RENDER" != true ]]; then
            render_quarto_documents
        fi
    fi
    
    if [[ "$SKIP_DOWNLOAD" != true ]]; then
        download_baseline
    fi
    
    # Compare files
    compare_rtf_files
    RESULT=$?
    
    # Cleanup
    if [[ "$CLEANUP_AUTO" == true ]]; then
        if [[ -d "$DIFF_DIR" ]] && [[ -n "$(ls -A "$DIFF_DIR")" ]]; then
            rm -rf "$QMD_DIR" "$OUTPUT_DIR" "$PY_DIR" "$RTF_DIR" "$BASELINE_DIR"
            echo "Automatic cleanup completed (differences preserved in $DIFF_DIR)"
        else
            rm -rf "$TEMP_BASE"
            echo "Automatic cleanup completed (all temp files removed)"
        fi
    elif [[ "$KEEP_TEMP" != true ]]; then
        cleanup
    else
        echo ""
        echo "Temporary files kept in: $TEMP_BASE"
    fi
    
    exit $RESULT
}

# Run main function
main "$@"