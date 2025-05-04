### Add table footnote and source

import pandas as pd
from rtflite import RTFDocument, RTFTitle, RTFPageFooter, RTFPageHeader,RTFFootnote, RTFSource

x = RTFFootnote(text=["footnote 1", "footnote 2"])

def df1():
    data = {
        "Column1": ["Data 1.1", "Data 2.1"],
        "Column2": ["Data 1.2", "Data 2.2"],
    }
    return pd.DataFrame(data)

df = RTFDocument(
        df=df1(), 
        rtf_title=RTFTitle(text=["title 1", "title 2"]),
        rtf_page_header=RTFPageHeader(text=["header 1", "header 2"]),
        rtf_page_footer=RTFPageFooter(text=["footer 1", "footer 2"]),
        rtf_footnote=RTFFootnote(text=["footnote 1", "footnote 2"]),
        rtf_source=RTFSource(text=["source 1", "source 2"]),
    )

df.write_rtf("test.rtf")