import fitz

def read_pdf_file(file_path):

    try:
        doc = fitz.open(file_path)
        text = ""

        for page in doc:
            try:
                text += page.get_text()
            except:
                continue  # ignore page cassée

        doc.close()

        if not text.strip():
            return "[PDF SCANNED or CORRUPTED - no text extracted]"

        return text

    except Exception as e:
        return f"[PDF ERROR] {str(e)}"