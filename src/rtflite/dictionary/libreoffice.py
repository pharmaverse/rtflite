"""LibreOffice-related constants and configurations."""

# Default paths to search for LibreOffice executable by platform
DEFAULT_PATHS = {
    "Darwin": [
        "/opt/homebrew/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    ],
    "Linux": [
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
        "/snap/bin/libreoffice",
        "/opt/libreoffice/program/soffice",
    ],
    "Windows": [
        r"C:\Program Files\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.com",
        r"C:\Program Files (x86)\LIBREO~1\program\soffice.com",
    ],
}

# Minimum required LibreOffice version
MIN_VERSION = "7.1"
