import cv2
import numpy as np
import os
import sys

def remove_gemini_watermark(input_path, output_path):
    """
    Removes the Gemini sparkle logo watermark from the bottom-right corner of an image.
    Uses OpenCV's inpainting method.
    """
    try:
        if not os.path.exists(input_path):
            return False, f"File {input_path} not found.", None

        # Load the image
        img = cv2.imread(input_path)
        if img is None:
            return False, "Could not read image.", None

        height, width = img.shape[:2]
        print(f"Processing image: {width}x{height}")

        # Gemini watermark is typically in the bottom-right corner.
        # Instead of a big blurry square, we'll only inpaint the logo pixels.
        
        # 1. Define a search area in the corner (adjust based on resolution)
        # 15% is generous enough to catch it
        search_size = int(max(width, height) * 0.15) 
        search_size = max(100, min(search_size, 400))
        
        # 2. Create a crop of just that corner
        x1, y1 = width - search_size, height - search_size
        roi = img[y1:height, x1:width]
        
        # 3. Create a mask of the logo (the sparkle)
        # Convert to gray
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Analyze brightness distribution
        p96 = np.percentile(gray_roi, 96)
        
        # Initial threshold guess
        if p96 > 170:
            threshold_val = min(p96 - 2, 250)
            print(f"Bright background. Initial threshold: {threshold_val}")
        else:
            threshold_val = 160
            print(f"Normal background. Initial threshold: {threshold_val}")

        # Iterative "Soft-Squeeze" Logic
        # We want the mask to be small (only the logo). 
        # If it's too big, we are selecting background. We squeeze (increase threshold) until it fits.
        
        roi_area = roi.shape[0] * roi.shape[1]
        max_allowed_area = int(roi_area * 0.025) # Max 2.5% of the corner (approx 2000px in 1024w)
        
        mask_roi = None
        
        # Loop to find the sweet spot
        for t in range(int(threshold_val), 256, 1):
             _, temp_mask = cv2.threshold(gray_roi, t, 255, cv2.THRESH_BINARY)
             
             # Basic noise filter
             kernel_noise = np.ones((2,2), np.uint8)
             temp_mask = cv2.morphologyEx(temp_mask, cv2.MORPH_OPEN, kernel_noise)
             
             count = cv2.countNonZero(temp_mask)
             
             if count <= max_allowed_area:
                 # Found a good threshold!
                 mask_roi = temp_mask
                 print(f"Locked threshold at {t} (Area: {count}px / {roi_area}px)")
                 break
        
        # Failsafe: If we exhausted the loop and mask is still None (shouldn't happen unless image is pure white)
        # or if we went to 255 and it was still too big (impossible for binary threshold except all 255)
        if mask_roi is None:
             # Just take what we have at 255 or empty
             mask_roi = np.zeros_like(gray_roi)

        # Dilate to cover edges/glow
        # We dilate a bit more if we used a high threshold, as we likely only caught the core.
        iterations = 3 if threshold_val > 200 else 2
        kernel = np.ones((3,3), np.uint8)
        mask_roi = cv2.dilate(mask_roi, kernel, iterations=iterations)
        
        # 4. Fallback Logic (CRITICAL)
        # If the mask is too small or empty (watermark wasn't brighter than background),
        # force a removal in the known location.
        if cv2.countNonZero(mask_roi) < 30: # Reduced from 50 as we are more selective now
            print("Watermark not detected by brightness. Using fallback box.")
            # Create a box mask in the expected location (bottom-right centered in ROI)
            # The logo is usually ~40-60px from the corner.
            box_size = 70
            offset = 10
            cv2.rectangle(mask_roi, 
                          (search_size - box_size - offset, search_size - box_size - offset), 
                          (search_size - offset, search_size - offset), 
                          255, -1)
        
        # 5. Fill the full image mask
        mask = np.zeros((height, width), dtype=np.uint8)
        mask[y1:height, x1:width] = mask_roi

        # 6. Apply inpainting - TELEA with radius 3 is a good balance
        result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

        # Save the result
        cv2.imwrite(output_path, result)

        return True, "Marca de agua de Gemini eliminada con éxito.", output_path

    except Exception as e:
        return False, f"Error processing image: {str(e)}", None

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python process_image_watermark.py <input_path> <output_path>")
        sys.exit(1)
    
    success, message, path = remove_gemini_watermark(sys.argv[1], sys.argv[2])
    print(message)
