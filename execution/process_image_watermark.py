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

        # Load Template
        # The template is the binary mask of the sparkles
        base_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(base_dir, "assets", "gemini_template_v2.png")
        
        if not os.path.exists(template_path):
            return False, "Template file not found. Please run extraction first.", None
            
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            return False, "Could not read template.", None
            
        th, tw = template.shape[:2]

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


        # 2. Multi-Scale Template Matching
        # The watermark size might vary depending on image resolution.
        # We will try a range of scales for the template.
        
        best_score = -1
        best_loc = None
        best_scale = 1.0
        best_mask_size = (0, 0)

        # Scales to try: 80% to 130% of original template size, in steps of 5%
        scales = np.linspace(0.8, 1.3, 11) 
        
        print("Starting multi-scale matching...")
        
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
        
        print(f"Best Scale: {best_scale:.2f}, Score: {best_score:.4f} at {best_loc}")
        
        # 3. Create Mask
        mask = np.zeros((height, width), dtype=np.uint8)
        
        # Threshold for detection confidence
        # slightly lower threshold can be safe if we have a good shape match mechanism, 
        # but 0.4 is standard. If we get 0.33 before, maybe with correct scale it goes up.
        # If it's still low, we might need to lower threshold or double check the template.
        detection_threshold = 0.38 
        
        if best_score > detection_threshold:
            # Match found! Place the template mask exactly there.
            top_left = best_loc
            t_w, t_h = best_mask_size
            
            # Translate ROI coords to global coords
            global_x = x1 + top_left[0]
            global_y = y1 + top_left[1]
            
            # Place the template (which is already a binary mask of the sparkles)
            # We treat the template itself as the mask to inpaint
            # Resize the original template to the best scale to use as mask
            resized_template_mask = cv2.resize(template, (t_w, t_h), interpolation=cv2.INTER_NEAREST)

            # Be careful with boundaries
            h_place = min(t_h, height - global_y)
            w_place = min(t_w, width - global_x)
            
            # Copy the template mask into the main mask
            mask[global_y:global_y+h_place, global_x:global_x+w_place] = resized_template_mask[0:h_place, 0:w_place]
            
            # Dilate slightly to ensure we cover the anti-aliased edges matches might miss
            # Dilate proportional to scale maybe?
            kernel_size = 3 if best_scale < 1.0 else 5
            kernel = np.ones((kernel_size, kernel_size), np.uint8)
            mask_roi_view = mask[global_y:global_y+h_place, global_x:global_x+w_place]
            dilated = cv2.dilate(mask_roi_view, kernel, iterations=2)
            mask[global_y:global_y+h_place, global_x:global_x+w_place] = dilated
            
            print("Watermark detected and mask placed.")
            
        else:
            # Fallback: If no match (weird), force a box in the corner?
            # Or just report failure? For robustness, let's do the "Unknown Box" fallback
            print("WARNING: Template not found (Score too low). Using fallback box.")
            box_size = 70
            box_x = width - 80
            box_y = height - 80
            cv2.rectangle(mask, (box_x, box_y), (box_x + box_size, box_y + box_size), 255, -1)

        # 4. Inpaint
        # Use a larger radius for inpainting to cover the complex text if needed, 
        # but 3 is usually good for small details.
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

        # Save
        cv2.imwrite(output_path, result)

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
