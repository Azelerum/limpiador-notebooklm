import fitz  # PyMuPDF
import os
import sys

def remove_watermarks(input_path, output_path):
    """
    Removes watermarks containing 'NotebookLM' from a PDF.
    NotebookLM watermarks are usually located at the bottom right.
    """
    try:
        if not os.path.exists(input_path):
            return False, f"File {input_path} not found.", None

        doc = fitz.open(input_path)
        watermarks_found = 0

        for page in doc:
            # Helper to get background color near the bottom-right corner
            # We sample a pixel slightly above the usual watermark area
            sample_x = page.rect.width - 160
            sample_y = page.rect.height - 60
            
            # Default to white
            bg_color = (1, 1, 1)
            try:
                # Create a tiny pixmap to sample the color
                pix = page.get_pixmap(clip=fitz.Rect(sample_x, sample_y, sample_x + 1, sample_y + 1))
                if pix.samples:
                    # Convert 0-255 to 0-1
                    pixel = pix.pixel(0, 0)
                    bg_color = tuple(c / 255.0 for c in pixel)
            except:
                pass

            # 1. Text-based search for 'NotebookLM'
            text_instances = page.search_for("NotebookLM")
            for inst in text_instances:
                page.add_redact_annot(inst, fill=bg_color)
                watermarks_found += 1
            
            # 2. Coordinate-based redaction (Bottom-Right Corner)
            rect_width = 150
            rect_height = 50
            margin = 5
            
            br_rect = fitz.Rect(
                page.rect.width - rect_width - margin,
                page.rect.height - rect_height - margin,
                page.rect.width - margin,
                page.rect.height - margin
            )
            
            page.add_redact_annot(br_rect, fill=bg_color)
            watermarks_found += 1
            
            # Apply redactions to permanently remove the content
            page.apply_redactions()

        if watermarks_found > 0:
            doc.save(output_path, garbage=4, deflate=True)
            doc.close()
            return True, f"Procesado con éxito. Se eliminaron {watermarks_found} marcas de agua de NotebookLM.", output_path
        else:
            doc.close()
            import shutil
            shutil.copy2(input_path, output_path)
            return True, "No se detectaron marcas de agua de NotebookLM. El archivo se devolvió original.", output_path

    except Exception as e:
        return False, f"Error processing PDF: {str(e)}", None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_pdf_watermark.py <input_path> <output_path>")
        sys.exit(1)
    
    success, message, path = remove_watermarks(sys.argv[1], sys.argv[2])
    print(message)
