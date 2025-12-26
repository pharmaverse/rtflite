from pathlib import Path
from unittest.mock import ANY, MagicMock, patch

import polars as pl
import pytest

from rtflite.encode import RTFDocument
from rtflite.input import RTFBody, RTFTitle

EXPORT_METHODS: list[tuple[str, str]] = [
    ("write_docx", "docx"),
    ("write_html", "html"),
    ("write_pdf", "pdf"),
]


@pytest.fixture
def sample_document() -> RTFDocument:
    """Create a small RTFDocument for export tests."""
    df = pl.DataFrame({"A": ["alpha"]})
    return RTFDocument(
        df=df,
        rtf_title=RTFTitle(text="Sample Title"),
        rtf_body=RTFBody(col_rel_width=[1]),
    )


@pytest.mark.parametrize(("method_name", "output_format"), EXPORT_METHODS)
@patch("rtflite.encode.LibreOfficeConverter")
def test_write_export_uses_provided_converter(
    mock_converter_cls,
    sample_document: RTFDocument,
    tmp_path: Path,
    method_name: str,
    output_format: str,
):
    """Verify that export methods use a provided converter instance."""
    converter = MagicMock()
    converter.convert.return_value = Path(f"dummy.{output_format}")

    output_path = tmp_path / f"output.{output_format}"

    with patch("rtflite.encode.shutil.move"):
        getattr(sample_document, method_name)(output_path, converter=converter)

    mock_converter_cls.assert_not_called()
    converter.convert.assert_called_once_with(
        input_files=ANY,
        output_dir=ANY,
        format=output_format,
        overwrite=True,
    )
    kwargs = converter.convert.call_args.kwargs
    assert isinstance(kwargs["output_dir"], Path)
    assert isinstance(kwargs["input_files"], Path)
    assert kwargs["input_files"].name == f"{output_path.stem}.rtf"


@pytest.mark.parametrize(("method_name", "output_format"), EXPORT_METHODS)
@patch("rtflite.encode.LibreOfficeConverter")
def test_write_export_creates_default_converter(
    mock_converter_cls,
    sample_document: RTFDocument,
    tmp_path: Path,
    method_name: str,
    output_format: str,
):
    """Verify that export methods create a default converter when omitted."""
    mock_instance = mock_converter_cls.return_value
    mock_instance.convert.return_value = Path(f"dummy.{output_format}")

    output_path = tmp_path / f"output.{output_format}"

    with patch("rtflite.encode.shutil.move"):
        getattr(sample_document, method_name)(output_path)

    mock_converter_cls.assert_called_once_with()
    mock_instance.convert.assert_called_once_with(
        input_files=ANY,
        output_dir=ANY,
        format=output_format,
        overwrite=True,
    )
    kwargs = mock_instance.convert.call_args.kwargs
    assert isinstance(kwargs["output_dir"], Path)
    assert isinstance(kwargs["input_files"], Path)
    assert kwargs["input_files"].name == f"{output_path.stem}.rtf"


@pytest.mark.parametrize(("method_name", "output_format"), EXPORT_METHODS)
@patch("rtflite.encode.LibreOfficeConverter")
def test_write_export_uses_temp_files(
    mock_converter_cls,
    sample_document: RTFDocument,
    tmp_path: Path,
    method_name: str,
    output_format: str,
):
    """Export methods should not write intermediate files into output dir."""
    mock_instance = mock_converter_cls.return_value

    def convert_side_effect(
        *, input_files: Path, output_dir: Path, format: str, overwrite: bool
    ) -> Path:
        out_path = Path(output_dir) / f"{Path(input_files).stem}.{format}"
        out_path.write_text("dummy output", encoding="utf-8")
        if format == "html":
            resources_dir = out_path.with_name(f"{out_path.name}_files")
            resources_dir.mkdir()
            (resources_dir / "resource.txt").write_text("resource", encoding="utf-8")
        return out_path

    mock_instance.convert.side_effect = convert_side_effect

    output_dir = tmp_path / "final"
    output_path = output_dir / f"report.{output_format}"

    getattr(sample_document, method_name)(output_path)

    assert output_path.exists()
    assert not any(path.suffix == ".rtf" for path in output_dir.iterdir())
    if output_format == "html":
        assert (output_dir / f"{output_path.name}_files").is_dir()

    kwargs = mock_instance.convert.call_args.kwargs
    assert kwargs["input_files"].parent != output_dir
    assert kwargs["output_dir"] != output_dir
