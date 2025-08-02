
# Function to convert all RTF files to PDF in batch
convert_rtf_to_pdf() {
    echo ""
    echo "=== Converting RTF files to PDF ==="

    # Create pdf directory if it doesn't exist
    mkdir -p docs/articles/pdf

    # Find all RTF files in the rtf directory
    if ls docs/articles/rtf/*.rtf 1> /dev/null 2>&1; then
        echo "Converting RTF files to PDF using rtflite converter..."

        # Use Python to batch convert RTF files
        cat > temp_convert.py << 'EOF'
import os
import glob
import subprocess
import rtflite as rtf

rtf_dir = "docs/articles/rtf"
pdf_dir = "docs/articles/pdf"

# Ensure PDF directory exists
os.makedirs(pdf_dir, exist_ok=True)

# Get RTF files that are in git changes (modified, added, staged, or untracked)
def get_changed_rtf_files():
    try:
        # Get staged files
        staged_result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                                     capture_output=True, text=True, check=True)
        staged_files = staged_result.stdout.strip().split('\n') if staged_result.stdout.strip() else []
        
        # Get modified files (unstaged changes)
        modified_result = subprocess.run(['git', 'diff', '--name-only'], 
                                       capture_output=True, text=True, check=True)
        modified_files = modified_result.stdout.strip().split('\n') if modified_result.stdout.strip() else []
        
        # Get untracked files
        untracked_result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                        capture_output=True, text=True, check=True)
        untracked_files = untracked_result.stdout.strip().split('\n') if untracked_result.stdout.strip() else []
        
        # Combine and filter for RTF files in the rtf directory
        all_changed_files = set(staged_files + modified_files + untracked_files)
        rtf_files = [f for f in all_changed_files 
                    if f.startswith('docs/articles/rtf/') and f.endswith('.rtf')]
        
        return rtf_files
    except subprocess.CalledProcessError as e:
        print(f"Error checking git status: {e}")
        return []

# Get only RTF files that have git changes
changed_rtf_files = get_changed_rtf_files()

if changed_rtf_files:
    print(f"Found {len(changed_rtf_files)} changed RTF files to convert:")
    try:
        converter = rtf.LibreOfficeConverter()
        for rtf_file in changed_rtf_files:
            rtf_name = os.path.basename(rtf_file)
            pdf_name = os.path.splitext(rtf_name)[0] + ".pdf"

            print(f"  Converting: {rtf_name} -> {pdf_name}")
            try:
                converter.convert(
                    input_files=rtf_file,
                    output_dir=pdf_dir,
                    format="pdf",
                    overwrite=True
                )
                print(f"    ✓ Success")
            except Exception as e:
                print(f"    ✗ Error: {str(e)}")
    except FileNotFoundError as e:
        print(f"LibreOffice not found: {e}")
        print("Please install LibreOffice to enable PDF conversion")
else:
    print("No changed RTF files found to convert")
EOF

        # Run the conversion script using the virtual environment Python
        if [ -f ".venv/bin/python" ]; then
            .venv/bin/python temp_convert.py
        else
            python3 temp_convert.py
        fi

        # Clean up
        rm temp_convert.py
    else
        echo "No RTF files found in docs/articles/rtf/"
    fi
}

# Main execution flow
echo ""
echo "=== Converting RTF files to PDF ==="

# Convert all RTF files to PDF in batch
convert_rtf_to_pdf