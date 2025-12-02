import os
import pytest
from rtflite import assemble_rtf, assemble_docx

@pytest.fixture
def sample_rtf_files(tmp_path):
    """Create sample RTF files for testing."""
    file1 = tmp_path / "test1.rtf"
    file2 = tmp_path / "test2.rtf"
    
    content1 = r"""{\rtf1\ansi\deff0
{\fonttbl{\f0 Arial;}}
{\colortbl;\red0\green0\blue0;}
\pard\plain\f0\fs24
Content of file 1
\par
}"""
    
    content2 = r"""{\rtf1\ansi\deff0
{\fonttbl{\f0 Arial;}}
{\colortbl;\red0\green0\blue0;}
\pard\plain\f0\fs24
Content of file 2
\par
}"""
    
    file1.write_text(content1, encoding="utf-8")
    file2.write_text(content2, encoding="utf-8")
    
    return [str(file1), str(file2)]

def test_assemble_rtf(sample_rtf_files, tmp_path):
    output_file = tmp_path / "combined.rtf"
    assemble_rtf(sample_rtf_files, str(output_file))
    
    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    
    # Check if content from both files is present
    assert "Content of file 1" in content
    assert "Content of file 2" in content
    
    # Check for page break
    assert r"\page" in content

def test_assemble_rtf_missing_file():
    with pytest.raises(FileNotFoundError):
        assemble_rtf(["non_existent.rtf"], "output.rtf")

def test_assemble_rtf_empty_list():
    with pytest.raises(ValueError):
        assemble_rtf([], "output.rtf")

def test_assemble_docx(sample_rtf_files, tmp_path):
    try:
        import docx
    except ImportError:
        pytest.skip("python-docx not installed")

    output_file = tmp_path / "combined.docx"
    assemble_docx(sample_rtf_files, str(output_file))
    
    assert output_file.exists()
    
    # Verify content using python-docx
    doc = docx.Document(str(output_file))
    
    # We expect INCLUDETEXT fields
    # python-docx doesn't easily expose field codes in paragraphs directly 
    # without inspecting XML, but we can check if paragraphs exist.
    assert len(doc.paragraphs) > 0
    
    # Check for "Table " text which we added
    found_table_caption = False
    for p in doc.paragraphs:
        if "Table " in p.text:
            found_table_caption = True
            break
    
    assert found_table_caption

def test_assemble_docx_landscape(sample_rtf_files, tmp_path):
    try:
        import docx
        from docx.enum.section import WD_ORIENT
    except ImportError:
        pytest.skip("python-docx not installed")

    output_file = tmp_path / "combined_landscape.docx"
    # Test with mixed orientation
    assemble_docx(sample_rtf_files, str(output_file), landscape=[False, True])
    
    assert output_file.exists()
    doc = docx.Document(str(output_file))
    
    # Check sections
    # We expect at least 2 sections (or 1 if no section break needed for last one, 
    # but our code adds section breaks)
    # Our code adds a section break for all but the last file, 
    # so for 2 files, we have 2 sections (one for first file, one for second).
    # Wait, code:
    # if i < len(input_files) - 1: doc.add_section()
    # So for 2 files:
    # i=0: add content, add section break.
    # i=1: add content.
    # Total sections: 2.
    
    assert len(doc.sections) == 2
    
    # First section should be portrait (default)
    assert doc.sections[0].orientation == WD_ORIENT.PORTRAIT
    
    # Second section should be landscape
    assert doc.sections[1].orientation == WD_ORIENT.LANDSCAPE

def test_assemble_docx_missing_file():
    try:
        import docx
    except ImportError:
        pytest.skip("python-docx not installed")
        
    with pytest.raises(FileNotFoundError):
        assemble_docx(["non_existent.rtf"], "output.docx")
