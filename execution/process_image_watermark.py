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
        
        # We look for bright pixels. The analysis showed max brightness ~207.
        # So we set a safe threshold of 160 to catch the glow and the core.
        _, mask_roi = cv2.threshold(gray_roi, 160, 255, cv2.THRESH_BINARY)
        
        # Dilate to cover edges/glow
        kernel = np.ones((3,3), np.uint8) # Smaller kernel for finer control
        mask_roi = cv2.dilate(mask_roi, kernel, iterations=2)
        
        # 4. Fallback Logic (CRITICAL)
        # If the mask is effectively empty (e.g. image is too dark or logo is blended),
        # we MUST force a removal in the known location.
        # Analysis showed the logo is about 50x50 pixels in a 1024 image (~5% of size).
        if cv2.countNonZero(mask_roi) < 50:
            # Create a box mask in the expected location (bottom-right centered in ROI)
            # The logo is usually ~40-60px from the corner.
            # We'll make a 60x60 box to be safe.
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
