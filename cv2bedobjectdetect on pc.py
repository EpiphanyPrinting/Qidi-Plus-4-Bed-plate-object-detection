import logging
import cv2
import urllib.request
import numpy as np
import os

import logging
import cv2
import urllib.request
import numpy as np
import os


import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

class MockGCode:
    def respond_info(self, message):
        print(f"GCode Response: {message}")

    def run_script_from_command(self, command):
        print(f"Executing GCode Command: {command}")


class TestBedChecker:
    def __init__(self):
        self.gcode = MockGCode()

    def cmd_check_object_on_bed(self, gcmd):
        try:
            # Sensitivity parameters
            threshold_value = 50  # Adjust for more/less sensitivity in thresholding
            min_contour_area = 50  # Adjust to filter out smaller objects
            use_adaptive_threshold = False  # Toggle adaptive thresholding

            # Load the empty bed and current bed images
            empty_bed_path_140 = "emptybed140.jpg"
            empty_bed_path_250 = "emptybed250.jpg"
            current_bed_path = "currentbed1.jpg"

            empty_bed_140 = cv2.imread(empty_bed_path_140)
            empty_bed_250 = cv2.imread(empty_bed_path_250)
            current_bed = cv2.imread(current_bed_path)

            if empty_bed_140 is None or empty_bed_250 is None or current_bed is None:
                self.gcode.respond_info("Error: Empty or current bed image not found.")
                return

            # Function to crop an image
            def crop_image(image):
                height, width = image.shape[:2]
                top = int(height * 0.45)
                bottom = height
                left = int(width * 0.20)
                right = int(width * 0.80)
                return image[top:bottom, left:right]

            # Function to enhance contrast using CLAHE (Adaptive Histogram Equalization)
            def enhance_contrast_clahe(image_gray):
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                return clahe.apply(image_gray)

            # Function to adjust lighting using LAB color space
            def adjust_lighting(image):
                lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                l, a, b = cv2.split(lab)
                l = cv2.equalizeHist(l)
                lab = cv2.merge((l, a, b))
                return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

            # Crop images
            empty_bed_140 = crop_image(empty_bed_140)
            empty_bed_250 = crop_image(empty_bed_250)
            current_bed = crop_image(current_bed)

            # Adjust lighting
            empty_bed_140 = adjust_lighting(empty_bed_140)
            empty_bed_250 = adjust_lighting(empty_bed_250)
            current_bed = adjust_lighting(current_bed)

            # Convert images to grayscale and enhance contrast
            empty_bed_gray_140 = enhance_contrast_clahe(cv2.cvtColor(empty_bed_140, cv2.COLOR_BGR2GRAY))
            empty_bed_gray_250 = enhance_contrast_clahe(cv2.cvtColor(empty_bed_250, cv2.COLOR_BGR2GRAY))
            current_bed_gray = enhance_contrast_clahe(cv2.cvtColor(current_bed, cv2.COLOR_BGR2GRAY))

            # Function to check for an object by comparing images with vertical shifts
            def check_for_object(empty_bed_gray, current_bed_gray, image_name):
                # Loop through vertical shifts from -20 to +20 pixels
                for vertical_shift in range(-20, 21):
                    shifted_bed = np.roll(empty_bed_gray, vertical_shift, axis=0)  # Apply vertical shift

                    diff = cv2.absdiff(shifted_bed, current_bed_gray)
                    diff = cv2.GaussianBlur(diff, (7, 7), 0)  # Increase kernel size for more smoothing

                    if use_adaptive_threshold:
                        block_size = max(11, (current_bed_gray.shape[0] // 10) | 1)  # Ensure odd number
                        thresh = cv2.adaptiveThreshold(diff, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                                    cv2.THRESH_BINARY, block_size, 2)
                    else:
                        _, thresh = cv2.threshold(diff, threshold_value, 255, cv2.THRESH_BINARY)

                    # Apply morphological operations to clean up noise
                    kernel = np.ones((3,3), np.uint8)
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)  # Fill small holes
                    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)   # Remove small noise

                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

                    # Smooth contours using approximation
                    for i in range(len(valid_contours)):
                        epsilon = 0.01 * cv2.arcLength(valid_contours[i], True)
                        valid_contours[i] = cv2.approxPolyDP(valid_contours[i], epsilon, True)

                    # Draw contours on the current bed image
                    contour_image = current_bed.copy()
                    cv2.drawContours(contour_image, valid_contours, -1, (0, 0, 255), 2)

                    if len(valid_contours) == 0:  # If no object is detected in this shift, consider it a match
                        return True  # Allow printing

                return False  # Object detected with no match

            # Step 1: Check empty_bed_140 against current_bed
            matches_140 = check_for_object(empty_bed_gray_140, current_bed_gray, "140")

            if matches_140:
                self.gcode.respond_info("Match found with emptybed140. Proceeding with print.")
                return  # Allow printing

            # Step 2: Check empty_bed_250 against current_bed (only if 140 did not match)
            matches_250 = check_for_object(empty_bed_gray_250, current_bed_gray, "250")

            if matches_250:
                self.gcode.respond_info("Match found with emptybed250. Proceeding with print.")
                return  # Allow printing

            # If neither 140 nor 250 matched, cancel the print
            self.gcode.respond_info(f"Object detected on the bed! Canceling print job...")
            self.gcode.run_script_from_command("CANCEL_PRINT")

        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")




# Run the test
if __name__ == "__main__":
    tester = TestBedChecker()
    tester.cmd_check_object_on_bed(None)  # `None` is passed since gcmd isn't used in the function