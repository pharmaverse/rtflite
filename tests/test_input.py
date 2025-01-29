from rtflite.encode import RTFDocument
from rtflite.input import RTFTitle

from .utils import ROutputReader, TestData

r_output = ROutputReader("test_input")


def test_rtf_encode_minimal():
    # ```{r, rtf_minimal}
    # tbl <- data.frame(
    #   `Column1` = c("Data 1.1", "Data 2.1"),
    #   `Column2` = c("Data 1.2", "Data 2.2")
    # )
    #
    # tbl_input <- tbl |>
    #   r2rtf::rtf_page() |>
    #   r2rtf::rtf_title(c("title 1", "title 2")) |>
    #   r2rtf::rtf_body()
    #
    # tbl_encode <- tbl_input |>
    #   r2rtf::rtf_encode(verbose = FALSE)
    #
    # tbl_encode |>
    #   r2rtf::write_rtf(tempfile()) |>
    #   readLines() |>
    #   cat(sep = "\n")
    # ```
    rtf_doc = RTFDocument(
        df=TestData.df1(), rtf_title=RTFTitle(text=["title 1", "title 2"])
    )

    assert rtf_doc.rtf_encode() == r_output.read("rtf_minimal")


def test_rtf_encode_with_title():
    # ```{r, rtf_title_line}
    # tbl <- data.frame(
    #   `Column 1` = c("Data 1.1", "Data 2.1"),
    #   `Column 2` = c("Data 1.2", "Data 2.2")
    # )
    #
    # tbl_input <- tbl |>
    #   r2rtf::rtf_title(c("title 1", "title 2")) |>
    #   r2rtf::rtf_body()
    #
    # tbl_encode <- tbl_input |>
    #   r2rtf::rtf_encode(verbose = TRUE)
    #
    # cat(tbl_encode$header, sep = "\n")
    # ```
    #
    # ```{r, rtf_page_line}
    # cat(tbl_encode$page, sep = "\n")
    # ```
    #
    # ```{r, rtf_page_margin_line}
    # cat(tbl_encode$margin, sep = "\n")
    # ```
    rtf_doc = RTFDocument(
        df=TestData.df1(), rtf_title=RTFTitle(text=["title 1", "title 2"])
    )
    assert rtf_doc._rtf_title_encode(method="line") == r_output.read("rtf_title_line")
    assert rtf_doc._rtf_page_encode() == r_output.read("rtf_page_line")
    assert rtf_doc._rtf_page_margin_encode() == r_output.read("rtf_page_margin_line")

    # Test text_font_size as a list
    rtf_doc = RTFDocument(
        df=TestData.df1(),
        rtf_title=RTFTitle(text=["title 1", "title 2"], text_font_size=[1, 2]),
    )
    assert rtf_doc.rtf_title.text_font_size == [1, 2]

    expected_output = "{\\pard\\hyphpar\\sb180\\sa180\\fi0\\li0\\ri0\\qc\\fs2{\\f0 title 1}\\line\\fs4{\\f0 title 2}\\par}"
    assert rtf_doc._rtf_title_encode(method="line") == expected_output
