from __future__ import annotations

from unittest.mock import patch

import pytest

from rtflite.convert import LibreOfficeConverter


def test_init_accepts_executable_path_as_path(tmp_path, monkeypatch):
    dummy_executable = tmp_path / "soffice"
    dummy_executable.write_text("")

    monkeypatch.setattr(LibreOfficeConverter, "_verify_version", lambda self: None)
    converter = LibreOfficeConverter(executable_path=dummy_executable)

    assert converter.executable_path == dummy_executable


def test_init_resolves_executable_name_via_which(tmp_path, monkeypatch):
    dummy_executable = tmp_path / "soffice"
    dummy_executable.write_text("")

    monkeypatch.setattr(LibreOfficeConverter, "_verify_version", lambda self: None)
    with patch("rtflite.convert.shutil.which", return_value=str(dummy_executable)):
        converter = LibreOfficeConverter(executable_path="soffice")

    assert converter.executable_path == dummy_executable


def test_init_raises_for_missing_explicit_path(tmp_path, monkeypatch):
    monkeypatch.setattr(LibreOfficeConverter, "_verify_version", lambda self: None)
    with pytest.raises(FileNotFoundError):
        LibreOfficeConverter(executable_path=tmp_path / "missing")


def test_init_raises_for_missing_command(monkeypatch):
    monkeypatch.setattr(LibreOfficeConverter, "_verify_version", lambda self: None)
    with (
        patch("rtflite.convert.shutil.which", return_value=None),
        pytest.raises(FileNotFoundError),
    ):
        LibreOfficeConverter(executable_path="soffice")
