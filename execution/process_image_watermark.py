import cv2
import numpy as np
import os
import sys

def remove_gemini_watermark(input_path, output_path, upscale=False):
    """
    Removes the Gemini sparkle logo watermark using Template Matching.
    Robust to any background brightness as it detects shape, not pixel value.
    Uses Texture Patching (Cloning) for the sparkle to preserve details like grain/carpet.
    """
    def apply_patch(img, local_mask, x, y, w, h):
        """Clones a nearby texture patch onto the target area using a mask."""
        height, width = img.shape[:2]
        # Bounding box of the masked region
        y1, y2 = max(0, y), min(height, y + h)
        x1, x2 = max(0, x), min(width, x + w)
        m_h, m_w = y2 - y1, x2 - x1
        if m_h <= 0 or m_w <= 0: return

        # Source patch: 1.2x width to the left
        sx = x1 - int(m_w * 1.3)
        if sx < 0: sx = x1 + int(m_w * 1.3) # Try right if left is off-screen
        if sx + m_w > width or sx < 0: return # Give up if no good source

        source_patch = img[y1:y2, sx:sx+m_w].copy()
        target_roi = img[y1:y2, x1:x2]
        m = local_mask[0:m_h, 0:m_w]
        
        # Feather the mask slightly for seamless blending (1px)
        m_float = m.astype(float) / 255.0
        m_blur = cv2.GaussianBlur(m_float, (3, 3), 0)
        
        for c in range(3):
            target_roi[:,:,c] = (target_roi[:,:,c] * (1.0 - m_blur) + source_patch[:,:,c] * m_blur).astype(np.uint8)

    try:
        if not os.path.exists(input_path):
            return False, f"File {input_path} not found.", None

        # Load image with alpha channel if present
        img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
        if img is None:
            return False, "Could not read image.", None

        # Handle different channel counts
        if len(img.shape) == 3 and img.shape[2] == 4:
            # RGBA
            alpha = img[:, :, 3]
            img_bgr = img[:, :, 0:3]
            is_rgba = True
        else:
            img_bgr = img
            is_rgba = False

        height, width = img_bgr.shape[:2]
        print(f"Processing image: {width}x{height} {'(RGBA)' if is_rgba else '(BGR)'}")

        # 1. Define Search Region (ROI) - Bottom Margin
        roi_h_pct = 0.15
        roi_h = int(height * roi_h_pct)
        roi_y = height - roi_h
        
        roi_bgr = img_bgr[roi_y:height, 0:width]
        roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

        # Enhance Contrast in ROI (handles faint/transparent watermarks)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        roi_gray_enhanced = clahe.apply(roi_gray)

        # 2. CREATE MASTER MASK
        mask = np.zeros((height, width), dtype=np.uint8)
        detected_anything = False

        # --- A. SPARKLE LOGO DETECTION (Template Matching) ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        
        templates = []
        if os.path.exists(assets_dir):
            for f in sorted(os.listdir(assets_dir), reverse=True): # V3 first
                if f.endswith(".png") and "template" in f and "mask" not in f:
                    t_path = os.path.join(assets_dir, f)
                    t_img = cv2.imread(t_path, cv2.IMREAD_GRAYSCALE)
                    if t_img is not None:
                        templates.append((f, t_img))
        
        best_sparkle_score = -1
        best_sparkle_loc = None
        best_sparkle_size = None
        best_sparkle_template = None

        # Only look for sparkle in the bottom-right corner (last 25% width)
        sparkle_search_w = int(width * 0.25)
        sparkle_roi_gray = roi_gray_enhanced[:, width-sparkle_search_w:]
        
        # We also use Edges (Canny) for shape matching if normal matching is low
        sparkle_roi_edges = cv2.Canny(sparkle_roi_gray, 50, 150)

        scales = np.linspace(0.4, 1.8, 30) 
        
        for t_name, template in templates:
            th, tw = template.shape[:2]
            t_edges = cv2.Canny(template, 50, 150)
            
            for scale in scales:
                t_w, t_h = int(tw * scale), int(th * scale)
                if t_w > sparkle_roi_gray.shape[1] or t_h > sparkle_roi_gray.shape[0]:
                    continue
                
                # Try Intensity Matching first
                resized_t = cv2.resize(template, (t_w, t_h), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(sparkle_roi_gray, resized_t, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                # If intensity match is weak, try Edge matching
                if max_val < 0.5:
                    resized_e = cv2.resize(t_edges, (t_w, t_h), interpolation=cv2.INTER_AREA)
                    res_e = cv2.matchTemplate(sparkle_roi_edges, resized_e, cv2.TM_CCOEFF_NORMED)
                    _, max_val_e, _, max_loc_e = cv2.minMaxLoc(res_e)
                    if max_val_e > max_val:
                        max_val = max_val_e
                        max_loc = max_loc_e

                if max_val > best_sparkle_score:
                    best_sparkle_score = max_val
                    best_sparkle_loc = max_loc
                    best_sparkle_size = (t_w, t_h)
                    best_sparkle_template = template

        if best_sparkle_score > 0.35:
            print(f"Sparkle detected (Score: {best_sparkle_score:.2f})")
            t_w, t_h = best_sparkle_size
            gx = (width - sparkle_search_w) + best_sparkle_loc[0]
            gy = roi_y + best_sparkle_loc[1]
            
            # Use the actual template as a mask for surgical precision
            s_mask = cv2.resize(best_sparkle_template, (t_w, t_h), interpolation=cv2.INTER_LINEAR)
            _, s_mask_bin = cv2.threshold(s_mask, 10, 255, cv2.THRESH_BINARY)
            
            h_p = min(t_h, height - gy)
            w_p = min(t_w, width - gx)
            
            # Minimal dilation to preserve background texture
            kernel = np.ones((3,3), np.uint8)
            s_mask_dilated = cv2.dilate(s_mask_bin, kernel, iterations=1)
            
            # Apply Texture Patching (instead of global inpainting later)
            apply_patch(img_bgr, s_mask_dilated, gx, gy, t_w, t_h)
            detected_anything = True
            # NOTE: We DON'T add this to the global 'mask' to avoid double-processing (blurring)
        
        # --- SURGICAL FALLBACK: FIXED POSITION ANCHORING ---
        # Gemini watermarks are almost always at ~94.5% Width, ~94.5% Height.
        # We apply the mask there if detection wasn't perfectly confident.
        if best_sparkle_score < 0.8:
             print("Applying Surgical Fixed-Position Anchor.")
             # Standard size for a 1024px image is about 50px
             standard_size = int(max(width, height) * 0.05)
             anchor_x = int(width * 0.945) - (standard_size // 2)
             anchor_y = int(height * 0.945) - (standard_size // 2)
             
             # Use the best available template (V3 if possible)
             fallback_template = templates[0][1] if templates else None
             if fallback_template is not None:
                 f_mask = cv2.resize(fallback_template, (standard_size, standard_size), interpolation=cv2.INTER_LINEAR)
                 _, f_mask_bin = cv2.threshold(f_mask, 10, 255, cv2.THRESH_BINARY)
                 
                 # Ensure we stay within bounds
                 y1, y2 = max(0, anchor_y), min(height, anchor_y + standard_size)
                 x1, x2 = max(0, anchor_x), min(width, anchor_x + standard_size)
                 m_h, m_w = y2 - y1, x2 - x1
                 f_mask_dilated = cv2.dilate(f_mask_bin, np.ones((3,3), np.uint8), iterations=2)
                 
                 if m_h > 0 and m_w > 0:
                     apply_patch(img_bgr, f_mask_dilated, anchor_x, anchor_y, standard_size, standard_size)
                     detected_anything = True

        # 4. INPAINT (Only for other detected features, if any)
        if not detected_anything:
            # Absolute last resort: just safety-box the corner
            print("No features detected. Applying safety box as fallback.")
            cv2.rectangle(mask, (width-100, height-100), (width-10, height-10), 255, -1)

        # Minimal final global dilation for remaining features in 'mask'
        mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=1)
        
        # Inpaint with Telea algorithm (radius reduced to 3)
        result_bgr = cv2.inpaint(img_bgr, mask, 3, cv2.INPAINT_TELEA)

        # 5. Restore Alpha channel if it was present
        if is_rgba:
            result = cv2.merge([result_bgr[:,:,0], result_bgr[:,:,1], result_bgr[:,:,2], alpha])
        else:
            result = result_bgr

        # Apply enhancement if requested
        if upscale:
            result = enhance_quality(result)

        # Save with high quality
        if output_path.lower().endswith('.png'):
            cv2.imwrite(output_path, result, [cv2.IMWRITE_PNG_COMPRESSION, 0])
        else:
            cv2.imwrite(output_path, result)

        msg = "Marcas de agua (Logo y Etiquetas) eliminadas correctamente."
        return True, msg, output_path

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error processing image: {str(e)}", None

def enhance_quality(img):
    """
    Advanced enhancement for text-heavy images.
    Uses denoising + high-fidelity upscaling + edge-preserving sharpening.
    """
    # 1. Initial Denoise (prevents upscaling compression artifacts)
    # Using a light bilateral filter to keep text edges sharp while cleaning backgrounds
    is_rgba = (len(img.shape) == 3 and img.shape[2] == 4)
    if is_rgba:
        bgr = img[:,:,0:3]
        alpha = img[:,:,3]
    else:
        bgr = img

    denoised = cv2.bilateralFilter(bgr, 7, 35, 35)

    # 2. High-Fidelity Upscale (2x)
    height, width = denoised.shape[:2]
    upscaled = cv2.resize(denoised, (width * 2, height * 2), interpolation=cv2.INTER_LANCZOS4)

    # 3. Edge-Preserving Sharpening (Detail Enhancement)
    # This makes text pop without creating the "ringing" or "blur" of standard sharpening
    enhanced = cv2.detailEnhance(upscaled, sigma_s=10, sigma_r=0.15)
    
    # 4. Final Polish: Contrast Adjustment
    # We use a Laplacian-based sharpen but very subtle
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]) * 0.05
    # The center is 1 + sum of others to maintain brightness
    kernel[1,1] = 1.0 + (0.05 * 8)
    final_bgr = cv2.filter2D(enhanced, -1, kernel)

    if is_rgba:
        # Restore and upscale alpha channel
        upscaled_alpha = cv2.resize(alpha, (width * 2, height * 2), interpolation=cv2.INTER_LANCZOS4)
        return cv2.merge([final_bgr[:,:,0], final_bgr[:,:,1], final_bgr[:,:,2], upscaled_alpha])
    
    return final_bgr

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_image_watermark.py <input_path> <output_path>")
        sys.exit(1)
    
    success, message, path = remove_gemini_watermark(sys.argv[1], sys.argv[2])
    print(message)
