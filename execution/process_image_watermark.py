import cv2
import numpy as np
import os
import sys

def remove_gemini_watermark(input_path, output_path, upscale=False):
    """
    Removes the Gemini sparkle logo watermark using Template Matching.
    Robust to any background brightness as it detects shape, not pixel value.
    """
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
        # We look at the bottom 15% for the sparkle and bottom 6% for author labels.
        roi_h_pct = 0.15
        roi_h = int(height * roi_h_pct)
        roi_y = height - roi_h
        
        roi_bgr = img_bgr[roi_y:height, 0:width]
        roi_gray = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2GRAY)

        # 2. CREATE MASTER MASK
        mask = np.zeros((height, width), dtype=np.uint8)
        detected_anything = False

        # --- A. SPARKLE LOGO DETECTION (Template Matching) ---
        base_dir = os.path.dirname(os.path.abspath(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        
        templates = []
        if os.path.exists(assets_dir):
            for f in os.listdir(assets_dir):
                if f.endswith(".png") and "template" in f:
                    t_path = os.path.join(assets_dir, f)
                    t_img = cv2.imread(t_path, cv2.IMREAD_GRAYSCALE)
                    if t_img is not None:
                        templates.append(t_img)
        
        best_sparkle_score = -1
        best_sparkle_loc = None
        best_sparkle_size = None
        best_sparkle_template = None

        # Dense scales to catch subtle variations
        scales = np.linspace(0.4, 1.6, 25) 
        
        # Only look for sparkle in the bottom-right corner (last 30% width)
        sparkle_search_w = int(width * 0.3)
        sparkle_roi_gray = roi_gray[:, width-sparkle_search_w:]
        
        for template in templates:
            th, tw = template.shape[:2]
            for scale in scales:
                t_w, t_h = int(tw * scale), int(th * scale)
                if t_w > sparkle_roi_gray.shape[1] or t_h > sparkle_roi_gray.shape[0]:
                    continue
                resized = cv2.resize(template, (t_w, t_h), interpolation=cv2.INTER_AREA)
                res = cv2.matchTemplate(sparkle_roi_gray, resized, cv2.TM_CCOEFF_NORMED)
                _, max_val, _, max_loc = cv2.minMaxLoc(res)
                
                if max_val > best_sparkle_score:
                    best_sparkle_score = max_val
                    best_sparkle_loc = max_loc
                    best_sparkle_size = (t_w, t_h)
                    best_sparkle_template = template

        if best_sparkle_score > 0.38:
            print(f"Sparkle detected (Score: {best_sparkle_score:.2f})")
            t_w, t_h = best_sparkle_size
            # Global coordinates
            gx = (width - sparkle_search_w) + best_sparkle_loc[0]
            gy = roi_y + best_sparkle_loc[1]
            
            # Draw sparkle mask
            s_mask = cv2.resize(best_sparkle_template, (t_w, t_h), interpolation=cv2.INTER_NEAREST)
            h_p = min(t_h, height - gy)
            w_p = min(t_w, width - gx)
            
            # Apply with dilation
            kernel = np.ones((3,3), np.uint8)
            iterations = 4 if best_sparkle_score > 0.7 else 2
            s_mask_dilated = cv2.dilate(s_mask, kernel, iterations=iterations)
            
            mask[gy:gy+h_p, gx:gx+w_p] = cv2.max(mask[gy:gy+h_p, gx:gx+w_p], s_mask_dilated[0:h_p, 0:w_p])
            detected_anything = True
        
        # --- SAFETY NET: FORCE BOTTOM RIGHT IF CONFIDENCE IS LOW ---
        # If we didn't find a super clear match (score > 0.7), or if we found nothing,
        # we nuke the corner anyway to be safe. The watermark is ALWAYS there.
        if best_sparkle_score < 0.7:
             print("Confidence low. Applying Safety Net to Bottom-Right Corner.")
             # Standard Gemini sparkle is about 50-70px in 1024px images
             safe_box_size = 75
             safe_x = width - safe_box_size - 10 # 10px padding from right
             safe_y = height - safe_box_size - 10 # 10px padding from bottom
             cv2.rectangle(mask, (safe_x, safe_y), (width, height), 255, -1)
             detected_anything = True

        # --- B. AUTHOR LABEL DETECTION (Detecting dark text labels) ---
        label_roi_h = int(height * 0.05)
        label_roi_y = height - label_roi_h
        label_roi = roi_gray[roi_h - label_roi_h:] 
        
        # Use Canny + Vertical Opening to find text (ignores horizontal borders)
        edges = cv2.Canny(label_roi, 50, 150)
        kernel_v = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
        text_strokes = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel_v)
        
        # Join strokes horizontally to restore words
        kernel_h = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
        text_clusters = cv2.dilate(text_strokes, kernel_h, iterations=3)
        
        contours, _ = cv2.findContours(text_clusters, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            # Author labels are typically wide but short, and NOT 100% of image width
            if (width * 0.8) > w > 30 and 4 < h < label_roi_h:
                print(f"Author label detected: {w}x{h} at x={x}")
                cv2.rectangle(mask, (x-5, label_roi_y + y - 3), (x + w + 5, label_roi_y + y + h + 5), 255, -1)
                detected_anything = True

        # --- C. TOP-HAT FALLBACK (Small bright icons missed by template) ---
        kh = 15
        kernel_th = cv2.getStructuringElement(cv2.MORPH_RECT, (kh, kh))
        tophat = cv2.morphologyEx(roi_gray, cv2.MORPH_TOPHAT, kernel_th)
        _, th_thresh = cv2.threshold(tophat, 180, 255, cv2.THRESH_BINARY)
        
        # Find small clusters in bottom right
        th_strip = th_thresh[:, width-sparkle_search_w:]
        cnts, _ = cv2.findContours(th_strip, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for c in cnts:
            if 10 < cv2.contourArea(c) < 1500:
                c_shifted = c + np.array([width-sparkle_search_w, roi_y])
                cv2.drawContours(mask, [c_shifted], -1, 255, -1)
                detected_anything = True

        # 4. INPAINT
        if not detected_anything:
            # Absolute last resort: just safety-box the corner
            print("No features detected. Applying safety box as fallback.")
            cv2.rectangle(mask, (width-100, height-100), (width-10, height-10), 255, -1)

        # Final Dilation to ensure edge blending
        mask = cv2.dilate(mask, np.ones((3,3), np.uint8), iterations=2)
        
        # Inpaint smoothly
        result_bgr = cv2.inpaint(img_bgr, mask, 5, cv2.INPAINT_NS)

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
