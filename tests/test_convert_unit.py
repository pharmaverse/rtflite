"""Converter regression tests that do not require LibreOffice."""

import subprocess
from pathlib import Path
from unittest.mock import Mock
from urllib.parse import unquote, urlparse

import pytest

from rtflite.convert import LibreOfficeConverter


@pytest.fixture
def executable(tmp_path: Path) -> Path:
    path = tmp_path / "soffice"
    path.touch()
    return path


@pytest.fixture
def converter(
    executable: Path, monkeypatch: pytest.MonkeyPatch
) -> LibreOfficeConverter:
    monkeypatch.setattr(LibreOfficeConverter, "_verify_version", lambda self: None)
    return LibreOfficeConverter(executable, timeout=5)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    path = tmp_path / "report.rtf"
    path.write_text(r"{\rtf1\ansi rtflite}")
    return path


def export(cmd: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Simulate the CLI output filename, including explicit export filters."""
    output_dir = Path(cmd[cmd.index("--outdir") + 1])
    extension = cmd[cmd.index("--convert-to") + 1].split(":", 1)[0]
    (output_dir / f"{Path(cmd[-1]).stem}.{extension}").write_bytes(b"new output")
    return subprocess.CompletedProcess(cmd, 0, "converted", "")


@pytest.mark.parametrize("version", ["7.1.0.3", "7.10.0.1", "24.8.3.2", "26.8.0.3"])
def test_supported_versions(executable: Path, monkeypatch: pytest.MonkeyPatch, version):
    run = Mock(
        return_value=subprocess.CompletedProcess([], 0, f"LibreOffice {version}")
    )
    monkeypatch.setattr("rtflite.convert.subprocess.run", run)
    LibreOfficeConverter(executable)
    assert run.call_args.kwargs["timeout"] == 120


@pytest.mark.parametrize(
    ("version", "error", "message"),
    [
        ("LibreOffice 7.0.6.2", RuntimeError, "below minimum"),
        ("unrecognized version", ValueError, "Can't parse"),
    ],
)
def test_invalid_versions(executable, monkeypatch, version, error, message):
    monkeypatch.setattr(
        "rtflite.convert.subprocess.run",
        Mock(return_value=subprocess.CompletedProcess([], 0, version)),
    )
    with pytest.raises(error, match=message):
        LibreOfficeConverter(executable)


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
def test_invalid_timeout(executable, timeout):
    with pytest.raises(ValueError, match="timeout"):
        LibreOfficeConverter(executable, timeout=timeout)


def test_version_timeout(executable, monkeypatch):
    monkeypatch.setattr(
        "rtflite.convert.subprocess.run",
        Mock(side_effect=subprocess.TimeoutExpired([str(executable)], 2)),
    )
    with pytest.raises(RuntimeError, match="version check timed out after 2"):
        LibreOfficeConverter(executable, timeout=2)


@pytest.mark.parametrize(
    "output_format",
    ["pdf", "pdf:writer_pdf_Export", "txt:Text (encoded):UTF8"],
)
def test_filter_output_filename(
    converter, source, tmp_path, monkeypatch, output_format
):
    run = Mock(side_effect=export)
    monkeypatch.setattr("rtflite.convert.subprocess.run", run)
    output_dir = tmp_path / "output"
    output = converter.convert(source, output_dir, format=output_format)
    assert output == output_dir / f"report.{output_format.split(':', 1)[0]}"
    assert output.read_bytes() == b"new output"
    cmd = run.call_args.args[0]
    assert cmd[cmd.index("--convert-to") + 1] == output_format
    assert run.call_args.kwargs["timeout"] == 5
    assert list(output_dir.iterdir()) == [output]


def test_isolated_profiles_and_absolute_paths(
    converter: LibreOfficeConverter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    source = Path("--report.rtf")
    source.write_text(r"{\rtf1\ansi rtflite}")
    profiles: list[Path] = []

    def record_profile(cmd, **kwargs):
        profile_arg = next(
            arg for arg in cmd if arg.startswith("-env:UserInstallation=")
        )
        profile_uri = profile_arg.split("=", 1)[1]
        output_dir = Path(cmd[cmd.index("--outdir") + 1])
        profile = output_dir.parent / "profile"
        assert profile_uri == profile.as_uri()
        assert "%20" in profile_uri and "%23" in profile_uri
        assert unquote(urlparse(profile_uri).path).endswith("/profile")
        assert Path(cmd[-1]).is_absolute()
        profiles.append(profile)
        return export(cmd, **kwargs)

    monkeypatch.setattr("rtflite.convert.subprocess.run", record_profile)
    output_dir = Path("output # with spaces")
    for _ in range(2):
        output = converter.convert(source, output_dir, overwrite=True)
        assert output == output_dir / "--report.pdf"
    assert profiles[0] != profiles[1]
    assert all(not profile.parent.exists() for profile in profiles)


@pytest.mark.parametrize("existing", [False, True])
def test_missing_output_fails_even_with_stale_file(
    converter, source, tmp_path, monkeypatch, existing
):
    output = tmp_path / "report.pdf"
    if existing:
        output.write_bytes(b"old output")
    monkeypatch.setattr(
        "rtflite.convert.subprocess.run",
        Mock(
            return_value=subprocess.CompletedProcess([], 0, "", "Could not load input")
        ),
    )
    with pytest.raises(RuntimeError, match="Could not load input"):
        converter.convert(source, tmp_path, overwrite=True)
    if existing:
        assert output.read_bytes() == b"old output"
    else:
        assert not output.exists()
    assert not list(tmp_path.glob(".rtflite-*"))


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (subprocess.TimeoutExpired([], 5), "conversion timed out after 5"),
        (
            subprocess.CalledProcessError(
                1, [], output="export started", stderr="failed"
            ),
            "export started[\\s\\S]*failed",
        ),
        (PermissionError("not executable"), "not executable"),
    ],
)
def test_process_failure_preserves_output(
    converter, source, tmp_path, monkeypatch, error, message
):
    output = tmp_path / "report.pdf"
    output.write_bytes(b"old output")

    def fail(cmd, **kwargs):
        export(cmd, **kwargs)  # A failed process may leave partial output.
        raise error

    monkeypatch.setattr("rtflite.convert.subprocess.run", fail)
    with pytest.raises(RuntimeError, match=message):
        converter.convert(source, tmp_path, overwrite=True)
    assert output.read_bytes() == b"old output"
    assert not list(tmp_path.glob(".rtflite-*"))


def test_overwrite_requires_opt_in(converter, source, tmp_path, monkeypatch):
    output = tmp_path / "report.pdf"
    output.write_bytes(b"old output")
    run = Mock(side_effect=export)
    monkeypatch.setattr("rtflite.convert.subprocess.run", run)
    with pytest.raises(FileExistsError):
        converter.convert(source, tmp_path)
    run.assert_not_called()
    converter.convert(source, tmp_path, overwrite=True)
    assert output.read_bytes() == b"new output"


def test_timeout_can_be_disabled(converter, source, tmp_path, monkeypatch):
    converter.timeout = None
    run = Mock(side_effect=export)
    monkeypatch.setattr("rtflite.convert.subprocess.run", run)
    converter.convert(source, tmp_path)
    assert run.call_args.kwargs["timeout"] is None


def test_html_companion_files(converter, source, tmp_path, monkeypatch):
    def export_html(cmd, **kwargs):
        result = export(cmd, **kwargs)
        output_dir = Path(cmd[cmd.index("--outdir") + 1])
        (output_dir / "report_html_image.png").write_bytes(b"image")
        resources = output_dir / "report.html_files"
        resources.mkdir()
        (resources / "image.png").write_bytes(b"nested image")
        return result

    monkeypatch.setattr("rtflite.convert.subprocess.run", export_html)
    output_dir = tmp_path / "output"
    converter.convert(source, output_dir, format="html")
    converter.convert(source, output_dir, format="html", overwrite=True)
    assert (output_dir / "report_html_image.png").read_bytes() == b"image"
    assert (
        output_dir / "report.html_files" / "image.png"
    ).read_bytes() == b"nested image"
    assert not list(output_dir.glob(".rtflite-*"))


def test_companion_collision_preserves_files(converter, source, tmp_path, monkeypatch):
    companion = tmp_path / "image.png"
    companion.write_bytes(b"old image")

    def export_html(cmd, **kwargs):
        result = export(cmd, **kwargs)
        output_dir = Path(cmd[cmd.index("--outdir") + 1])
        (output_dir / companion.name).write_bytes(b"new image")
        return result

    monkeypatch.setattr("rtflite.convert.subprocess.run", export_html)
    with pytest.raises(FileExistsError, match="image.png"):
        converter.convert(source, tmp_path, format="html")
    assert companion.read_bytes() == b"old image"
    assert not (tmp_path / "report.html").exists()


@pytest.mark.parametrize(
    "output_format", ["", ".pdf", "../pdf", "pdf/file", "pdf\\file"]
)
def test_invalid_format(converter, source, tmp_path, output_format):
    with pytest.raises(ValueError, match="format must be"):
        converter.convert(source, tmp_path, format=output_format)


def test_directory_input_rejected(converter, tmp_path):
    with pytest.raises(FileNotFoundError):
        converter.convert(tmp_path, tmp_path / "output")
