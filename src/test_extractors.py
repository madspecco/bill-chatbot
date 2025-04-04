import time
import fitz  # pymupdf
import pdfplumber
import pandas as pd
import pytesseract
from pdf2image import convert_from_path

def extract_text_with_pdfminer(pdf_path):
    """Extract text and tables from a PDF using pdfplumber."""
    start_time = time.time()
    text, tables = "", []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
                tables.extend(page.extract_tables())

        return {
            "method": "pdfminer (pdfplumber)",
            "text": text,
            "tables": [pd.DataFrame(t) for t in tables if t],
            "table_count": len(tables),
            "processing_time": round(time.time() - start_time, 2)
        }
    except Exception as e:
        return {"method": "pdfminer", "error": str(e), "text": "", "tables": []}

def extract_text_with_pymupdf(pdf_path):
    """Extract text and tables from a PDF using PyMuPDF."""
    start_time = time.time()
    text, tables = "", []

    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
            
            tab = page.find_tables()
            if tab.tables:
                for idx, table in enumerate(tab.tables):
                    markdown_table = table.to_markdown()
                    tables.append(markdown_table)

        return {
            "method": "pymupdf",
            "text": text,
            "tables": tables,
            "table_count": len(tables),
            "processing_time": round(time.time() - start_time, 2)
        }
    except Exception as e:
        return {
            "method": "pymupdf",
            "error": str(e),
            "text": "",
            "tables": [],
            "table_count": 0,
            "processing_time": round(time.time() - start_time, 2)
        }

def extract_with_ocr_based_layout(pdf_path):
    """Extract text and detect tables using OCR."""
    start_time = time.time()
    text, ocr_tables = "", []

    try:
        images = convert_from_path(pdf_path)
        for img in images:
            text += pytesseract.image_to_string(img, config='--oem 3 --psm 6') + "\n"
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DATAFRAME)
            data = data[data.text.notna()]

            if not data.empty:
                data['line_group'] = data['top'] // 10
                table_data = [group_data.sort_values('left')['text'].tolist() for _, group_data in data.groupby('line_group')]
                if len(table_data) > 1:
                    ocr_tables.append(pd.DataFrame(table_data))

        return {
            "method": "OCR",
            "text": text,
            "tables": ocr_tables,
            "table_count": len(ocr_tables),
            "processing_time": round(time.time() - start_time, 2)
        }
    except Exception as e:
        return {"method": "OCR", "error": str(e), "text": "", "tables": []}

def compare_extraction_methods(pdf_path):
    """Runs multiple extraction methods on a given PDF."""
    return [
        extract_text_with_pdfminer(pdf_path),
        extract_text_with_pymupdf(pdf_path),
        # extract_with_ocr_based_layout(pdf_path),
    ]
