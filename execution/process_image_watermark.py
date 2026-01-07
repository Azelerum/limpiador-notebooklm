import cv2
import numpy as np
import os
import sys

def remove_gemini_watermark(input_path, output_path):
    """
    Removes the Gemini sparkle logo watermark using Template Matching.
    Robust to any background brightness as it detects shape, not pixel value.
    """
    try:
        if not os.path.exists(input_path):
            return False, f"File {input_path} not found.", None

        # Load image
        img = cv2.imread(input_path)
        if img is None:
            return False, "Could not read image.", None



        height, width = img.shape[:2]
        print(f"Processing image: {width}x{height}")

        # 1. Define Search Region (ROI) - Bottom Right Corner
        # The logo is always in the same relative spot.
        roi_scale = 0.15 # 15% of size
        search_size = int(max(width, height) * roi_scale)
        search_size = max(150, min(search_size, 400)) # Clamped size
        
        x1 = width - search_size
        y1 = height - search_size
        
        # Ensure ROI is valid
        if x1 < 0 or y1 < 0:
            x1, y1 = 0, 0
            
        roi = img[y1:height, x1:width]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

        # 2. Ensemble Template Matching
        # We will try multiple templates and multiple scales.
        
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
        
        if not templates:
            print("No templates found in assets! using fallback.")
        else:
            print(f"Loaded {len(templates)} templates.")

        best_score = -1
        best_loc = None
        best_scale = 1.0
        best_mask_size = (0, 0)
        best_template = None

        # Scales to try: 70% to 130%
        scales = np.linspace(0.7, 1.3, 13) 
        
        print("Starting ensemble matching...")
        
        for template in templates:
            th, tw = template.shape[:2]
            for scale in scales:
                # Resize template
                t_w = int(tw * scale)
                t_h = int(th * scale)
                
                # If resized template is larger than ROI, skip
                if t_w > gray_roi.shape[1] or t_h > gray_roi.shape[0]:
                    continue
                    
                resized_template = cv2.resize(template, (t_w, t_h), interpolation=cv2.INTER_AREA)
                
                # Match
                res = cv2.matchTemplate(gray_roi, resized_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                
                if max_val > best_score:
                    best_score = max_val
                    best_loc = max_loc
                    best_scale = scale
                    best_mask_size = (t_w, t_h)
                    best_template = template
        
        print(f"Best Ensemble Result: Scale: {best_scale:.2f}, Score: {best_score:.4f}")
        
        # 3. Create Mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Threshold for detection confidence
        # lower threshold allowed if we have good shape match
        detection_threshold = 0.38 
        
        if best_score > detection_threshold:
            # Match found! 
            top_left = best_loc
            t_w, t_h = best_mask_size
            
            global_x = x1 + top_left[0]
            global_y = y1 + top_left[1]
            
            # Resize the best template to the best scale
            resized_template_mask = cv2.resize(best_template, (t_w, t_h), interpolation=cv2.INTER_NEAREST)

            h_place = min(t_h, height - global_y)
            w_place = min(t_w, width - global_x)
            
            mask[global_y:global_y+h_place, global_x:global_x+w_place] = resized_template_mask[0:h_place, 0:w_place]
            
            # Dilate
            kernel_size = 3 if best_scale < 1.0 else 5
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            mask_roi_view = mask[global_y:global_y+h_place, global_x:global_x+w_place]
            dilated = cv2.dilate(mask_roi_view, kernel, iterations=2)
            mask[global_y:global_y+h_place, global_x:global_x+w_place] = dilated
            
            print("Watermark detected via Template Matching.")
            
        else:
            # FALLBACK: Bright Spot Detection
            print("Template matching weak. Trying Bright Spot Fallback...")
            
            # Threshold the ROI to find bright spots (Gemini sparkles are usually white/bright)
            # Use a high threshold
            _, binary_roi = cv2.threshold(gray_roi, 230, 255, cv2.THRESH_BINARY)
            
            # Filter noise
            kernel = np.ones((3,3), np.uint8)
            binary_roi = cv2.morphologyEx(binary_roi, cv2.MORPH_OPEN, kernel, iterations=1)
            
            # Find contours
            contours, _ = cv2.findContours(binary_roi, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Look for contours that might be the watermark (near center of ROI usually, but could be anywhere in bottom right)
            found_spot = False
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if 10 < area < 2000: # Reasonable size for a sparkle
                    # Draw this contour on the global mask
                    # Need to shift coordinates
                    cnt_shifted = cnt + np.array([x1, y1])
                    cv2.drawContours(mask, [cnt_shifted], -1, 255, -1)
                    found_spot = True
            
            if found_spot:
                 # Dilate the fallback mask to be safe
                kernel = np.ones((5,5), np.uint8)
                mask = cv2.dilate(mask, kernel, iterations=2)
                print("Watermark detected via Bright Spot Fallback.")
            else:
                # Last resort: Box
                print("WARNING: No watermark detected. Using Safety Box.")
                box_size = 70
                box_x = width - 80
                box_y = height - 80
                cv2.rectangle(mask, (box_x, box_y), (box_x + box_size, box_y + box_size), 255, -1)

        # 4. Inpaint
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

        # Save
        cv2.imwrite(output_path, result)

        return True, f"Marca de agua de Gemini eliminada (Score: {best_score:.2f}).", output_path

        return True, f"Marca de agua de Gemini eliminada (Scale: {best_scale:.2f}, Score: {best_score:.2f}).", output_path

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"Error processing image: {str(e)}", None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_image_watermark.py <input_path> <output_path>")
        sys.exit(1)
    
    success, message, path = remove_gemini_watermark(sys.argv[1], sys.argv[2])
    print(message)
