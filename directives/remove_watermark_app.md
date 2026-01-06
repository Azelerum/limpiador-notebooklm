# Remove NotebookLM Watermark - Web App (PDF)

## Goal
Deploy a simple web application that allows users to upload NotebookLM documents (PDF) and download versions with watermarks removed.

## Inputs
- User uploads a file (.pdf format)
- User clicks "Eliminar marcas de agua" button

## Tools/Scripts to Use
- `execution/process_pdf_watermark.py` - Core processing script that removes watermarks from PDF files
- `execution/web_app_server.py` - Flask/FastAPI server that handles uploads and serves the web interface
- Web interface files in `web/` directory

## Process Flow
1. User uploads .pdf file via web interface
2. File is saved temporarily in `.tmp/uploads/`
3. `process_pdf_watermark.py` is called with file path
4. Processed file is saved to `.tmp/processed/`
5. User receives download link for cleaned file
6. Temporary files are cleaned up after download or timeout

## Outputs
- **Deliverable**: Web application accessible via localhost
- **Intermediates**: Original uploads in `.tmp/uploads/`, processed files in `.tmp/processed/`

## Edge Cases
- Invalid file format (non-PDF) → show error message
- File too large (>50MB) → reject with message
- Scanned PDF (image only) → warn user that text-based removal might not work
- No watermarks found → return original

## Technical Requirements
- Clean, minimal UI with large title "Elimina marcas de agua de NotebookLM"
- Redact or remove text "NotebookLM" from pages
- Automatic cleanup of files older than 1 hour in `.tmp/`
