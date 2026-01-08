import cv2
import numpy as np
import os

def extract_template(input_path, output_path):
    img = cv2.imread(input_path)
    if img is None:
        print("Error loading image")
        return
    
    # The logo has color. Let's isolate the non-checkerboard parts.
    # Checkerboard is usually gray/white.
    # We can use the saturation channel in HSV to isolate the blue parts.
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    s = hsv[:,:,1]
    v = hsv[:,:,2]
    
    # Isolate the sparkle. It's colorful OR very bright.
    _, mask_s = cv2.threshold(s, 20, 255, cv2.THRESH_BINARY)
    _, mask_v = cv2.threshold(v, 200, 255, cv2.THRESH_BINARY)
    mask = cv2.bitwise_or(mask_s, mask_v)
    
    # Find the largest contour
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        print("No contours found")
        return
    
    cnt = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(cnt)
    
    # Crop and save as grayscale template
    sparkle_crop = v[y:y+h, x:x+w]
    
    # Also create a binary mask template
    _, binary_mask = cv2.threshold(sparkle_crop, 10, 255, cv2.THRESH_BINARY)
    
    cv2.imwrite(output_path, sparkle_crop)
    cv2.imwrite(output_path.replace(".png", "_mask.png"), binary_mask)
    print(f"Template saved to {output_path}")

if __name__ == "__main__":
    extract_template("/Users/jacobo/.gemini/antigravity/brain/0735f359-092b-4e18-af1e-0a9278bfcc16/uploaded_image_1767859733627.jpg", "/Users/jacobo/00.git/01.gitea-jacobo/ag-eliminar-marca-agua/execution/assets/gemini_template_v3.png")
