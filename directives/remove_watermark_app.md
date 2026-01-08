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
- **Strategy: Template Matching (Advanced Recognizer)**:
  - We use an ensemble of templates (sparkle logos) at multiple scales (0.7 to 1.3).
  - This is robust to any background (snow, city, dark) because it detects the *shape* and not just the *brightness*.
- **Inpainting**:
  - Once detected, we use Navier-Stokes (NS) inpainting for a smoother blend.
- **Resolution Policy**: 
  - **Original Quality (Fixed)**: We explicitly avoid upscaling or artificial sharpening filters. 
  - The tool outputs the exact same dimensions and byte-fidelity as the input to avoid "blurry" or "AI-distorted" artifacts in text or textures.
- **Fallback**: 
  - If shape matching fails, we use a **Top-Hat Transform** (local contrast detector) as a secondary layer.
  - Final resort: known safety bounding box.

## Technical Requirements
- Clean, drop-zone UI.
- Fast processing (<3s).
- Robust error handling for bad file types.

