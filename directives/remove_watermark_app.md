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
- **Goal**: Preserve original image integrity while removing the logo.
- **Watermark**: "Sparkle" logo in the bottom-right corner.
- **Strategy: Surgical Shape-Based Removal**:
  - We use an ensemble of templates (including `v3` for high-fidelity) at multiple scales.
  - **Surgical Anchoring (Primary/Fallback)**: Since Gemini watermarks have a fixed position (~94.5% Width, ~94.5% Height), we use a high-precision binary shape mask centered at this exact coordinate.
  - This is robust to any background (snow, city, dark) and perfectly preserves transparency and surrounding textures.
- **Inpainting**:
  - We use Navier-Stokes (NS) inpainting limited strictly to the sparkle pixels to ensure a seamless blend.
- **Resolution Policy**: 
  - **Original Quality (Fixed)**: We explicitly avoid upscaling or artificial sharpening filters. 
  - The tool outputs the exact same dimensions and byte-fidelity as the input.
- **Author Label Detection**:
  - Uses Canny edge detection + morphological clusters to isolate and surgically remove photographer/credit text labels in the bottom margin.

## Technical Requirements
- Clean, drop-zone UI.
- Fast processing (<3s).
- Robust error handling for bad file types.

