import pytest

from rtflite.strwidth import (
    RTF_FONT_NAMES,
    RTF_FONT_NUMBERS,
    FontName,
    FontNumber,
    get_string_width,
)

# Test strings with known characteristics
TEST_STRINGS = {
    "empty": "",
    "single": "a",
    "mixed": "Hello, World!",
    "spaces": "  spaces  ",
    "numbers": "12345",
}

# Sample of fonts to test (both names and numbers)
TEST_FONT_NAMES: list[FontName] = [
    "Times New Roman",
    "Arial",
    "Courier New",
]

# Corresponding numbers for the test fonts
TEST_FONT_NUMBERS: list[FontNumber] = [
    1,
    4,
    9,
]


def test_basic_width_calculation():
    """Test that width increases with string length."""
    width_empty = get_string_width("")
    width_single = get_string_width("a")
    width_multiple = get_string_width("aaa")

    assert width_empty < width_single
    assert width_single < width_multiple
    assert width_multiple > width_empty


def test_different_fonts_by_name():
    """Test that different fonts give different widths using font names."""
    test_string = "Test String"
    widths = {
        font: get_string_width(test_string, font=font) for font in TEST_FONT_NAMES
    }

    # Monospace should be wider than proportional fonts
    assert widths["Courier New"] > widths["Times New Roman"]
    assert widths["Courier New"] > widths["Arial"]


def test_different_fonts_by_number():
    """Test that different fonts give different widths using font numbers."""
    test_string = "Test String"
    widths = {num: get_string_width(test_string, font=num) for num in TEST_FONT_NUMBERS}

    # Monospace (9) should be wider than proportional fonts (1 and 4)
    assert widths[9] > widths[1]  # Courier New > Times New Roman
    assert widths[9] > widths[4]  # Courier New > Arial


def test_font_sizes():
    """Test that font size affects width proportionally."""
    test_string = "Test"
    # Test with both name and number
    width_10pt_name = get_string_width(test_string, font="Arial", font_size=10)
    width_20pt_name = get_string_width(test_string, font="Arial", font_size=20)
    width_10pt_num = get_string_width(test_string, font=4, font_size=10)  # Arial
    width_20pt_num = get_string_width(test_string, font=4, font_size=20)

    # Allow for small rounding differences
    assert pytest.approx(width_20pt_name / width_10pt_name, rel=0.1) == 2.0
    assert pytest.approx(width_20pt_num / width_10pt_num, rel=0.1) == 2.0


def test_font_name_number_equivalence():
    """Test that font names and numbers give identical results."""
    test_string = "Test String"
    for font_name, font_number in RTF_FONT_NUMBERS.items():
        width_by_name = get_string_width(test_string, font=font_name)
        width_by_number = get_string_width(test_string, font=font_number)
        assert width_by_name == width_by_number


def test_invalid_inputs():
    """Test error handling for invalid inputs."""
    # Invalid font name
    with pytest.raises(ValueError):
        get_string_width("Test", font="NonexistentFont")  # type: ignore

    # Invalid font number
    with pytest.raises(ValueError):
        get_string_width("Test", font=11)  # type: ignore

    # Invalid unit
    with pytest.raises(ValueError):
        get_string_width("Test", unit="invalid")  # type: ignore


@pytest.mark.parametrize(
    "font_name",
    [
        "Times New Roman",
        "Times New Roman Greek",
        "Arial Greek",
        "Arial",
        "Helvetica",
        "Calibri",
        "Georgia",
        "Cambria",
        "Courier New",
        "Symbol",
    ],
)
def test_all_supported_font_names(font_name: FontName):
    """Test that all supported font names work without raising exceptions."""
    result = get_string_width("Test", font=font_name)
    assert isinstance(result, float)
    assert result > 0


@pytest.mark.parametrize("font_number", range(1, 11))
def test_all_supported_font_numbers(font_number: FontNumber):
    """Test that all supported font numbers work without raising exceptions."""
    result = get_string_width("Test", font=font_number)
    assert isinstance(result, float)
    assert result > 0


@pytest.mark.parametrize("test_string", TEST_STRINGS.values())
def test_various_string_types(test_string: str):
    """Test different types of strings with both font name and number."""
    # Test with font name
    width_name = get_string_width(test_string, font="Times New Roman")
    assert isinstance(width_name, float)
    # Test with font number
    width_num = get_string_width(test_string, font=1)  # Times New Roman
    assert isinstance(width_num, float)

    if test_string:
        assert width_name > 0
        assert width_num > 0
    else:
        assert width_name == 0
        assert width_num == 0


def test_rtf_font_mappings():
    """Test that RTF font mappings are complete and consistent."""
    # Check that all numbers have corresponding names
    for number in range(1, 11):
        assert number in RTF_FONT_NAMES

    # Check that all names have corresponding numbers
    for name in RTF_FONT_NAMES.values():
        assert name in RTF_FONT_NUMBERS

    # Check bidirectional mapping consistency
    for name, number in RTF_FONT_NUMBERS.items():
        assert RTF_FONT_NAMES[number] == name
