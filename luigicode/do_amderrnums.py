# This script extracts the errata numbers for AMD documents.

import camelot
import os

# Pages in which the errata are detailed in errata documents.
cpu_pages = {
    "amd_10h":    "30-34",
    "amd_11h":    "14",
    "amd_12h":    "18-19",
    "amd_14h":    "18-20",
    "amd_15h_00": "14-17",
    "amd_15h_10": "14-15",
    "amd_15h_30": "13",
    "amd_15h_70": "12",
    "amd_16h_00": "13",
    "amd_16h_30": "12",
    "amd_17h_00": "12-13",
    "amd_17h_30": "11-12",
    "amd_19h":    "11-12",
}

filepath_root = "errata_documents/amd"

for cpu_name, pages in cpu_pages.items():
    filepath = os.path.join(filepath_root, "{}.pdf".format(cpu_name))
    tables = camelot.read_pdf(filepath, pages=pages)
    print(cpu_name)
    for table in tables:
        for row in table.data:
            if row[0].strip().isdigit():
                print(row[0])
    print()
