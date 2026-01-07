# Remove Watermark App (NotebookLM PDF & Gemini Images)

## Goal
Deploy a simple web application that allows users to upload NotebookLM documents (PDF) and Gemini-generated images, removing their respective watermarks automatically.

## Inputs
- User uploads a file (.pdf, .jpg, .png)
- User clicks "Eliminar marcas de agua" button

## Tools/Scripts to Use
- `execution/process_pdf_watermark.py` - Core processing script for PDFs (NotebookLM).
- `execution/process_image_watermark.py` - Core processing script for Images (Gemini/Bard).
- `execution/web_app_server.py` - Flask server handling uploads and routing.
- Web interface files in `web/` directory.

## Process Flow
1. User uploads file via web interface.
2. Server determines file type.
    - **PDF**: Calls `process_pdf_watermark.py`
    - **Image**: Calls `process_image_watermark.py`
3. Processed file saved to `.tmp/processed/`.
4. User receives download link.
5. Auto-cleanup of temps.

## Outputs
- **Deliverable**: Web application accessible via localhost (and deployable to Render).
- **Intermediates**: Original uploads in `.tmp/uploads/`, processed files in `.tmp/processed/`.

## Learnings & Edge Cases

### PDF (NotebookLM)
- Watermark is text-based ("NotebookLM").
- Strategy: Seek text object in bottom of pages and obscure/delete.

### Images (Gemini/Bard)
- Watermark is a "sparkle" logo in the bottom-right.
- **Dynamic Thresholding (Self-Annealing)**:
  - Originally used fixed threshold (160). Failed on bright backgrounds.
  - **New Logic (Iterative Soft-Squeeze)**: 
    1. Calculate 96th percentile.
    2. Set initial high threshold (up to 250).
    3. **Constraint Loop**: Measure mask size. If > 2.5% of ROI area, increase threshold by 1 and retry. Repeat until mask is small (<2.5%) or limit reached.
    4. This prevents massive blurs on white/snowy images where background brightness is almost identical to the watermark.
  - Fallback: known bounding box.

## Technical Requirements
- Clean, drop-zone UI.
- Fast processing (<3s).
- Robust error handling for bad file types.

