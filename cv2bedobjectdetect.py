import logging
import cv2
import urllib.request
import numpy as np
import os

class cv2_bed_object_detect:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")

        # Register the custom G-code commands
        self.gcode.register_command("CAPTURE_IMAGE_EMPTY_BED_140", self.cmd_capture_image_empty_bed_140, desc="Capture an image from the webcam with an empty bed")
        self.gcode.register_command("CAPTURE_IMAGE_EMPTY_BED_250", self.cmd_capture_image_empty_bed_250, desc="Capture an image from the webcam with an empty bed")
        self.gcode.register_command("CAPTURE_IMAGE_CURRENT_BED", self.cmd_capture_image_current_bed, desc="Capture an image from the webcam of the current bed")
        self.gcode.register_command("CHECK_OBJECT_ON_BED", self.cmd_check_object_on_bed, desc="Check if there is an object on the bed by comparing to empty bed")

    def cmd_capture_image_empty_bed_140(self, gcmd):
        try:
            stream_url = "http://localhost:8080/?action=snapshot"  # Default URL for mjpg-streamer
            resp = urllib.request.urlopen(stream_url)  # Open the URL
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)  # Read and convert to array
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)  # Decode image
            
            if frame is not None:
                # Save the empty bed image
                empty_bed_path = "/home/mks/opencvtest/emptybed140.jpg"
                cv2.imwrite(empty_bed_path, frame)
                self.gcode.respond_info(f"Empty bed image captured and saved to {empty_bed_path}")
            else:
                self.gcode.respond_info("Error: Failed to decode image")
        
        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")
    def cmd_capture_image_empty_bed_250(self, gcmd):
        try:
            stream_url = "http://localhost:8080/?action=snapshot"  # Default URL for mjpg-streamer
            resp = urllib.request.urlopen(stream_url)  # Open the URL
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)  # Read and convert to array
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)  # Decode image
            
            if frame is not None:
                # Save the empty bed image
                empty_bed_path = "/home/mks/opencvtest/emptybed250.jpg"
                cv2.imwrite(empty_bed_path, frame)
                self.gcode.respond_info(f"Empty bed image captured and saved to {empty_bed_path}")
            else:
                self.gcode.respond_info("Error: Failed to decode image")
        
        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")
    
    def cmd_capture_image_current_bed(self, gcmd):
        try:
            stream_url = "http://localhost:8080/?action=snapshot"  # Default URL for mjpg-streamer
            resp = urllib.request.urlopen(stream_url)  # Open the URL
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)  # Read and convert to array
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)  # Decode image
            
            if frame is not None:
                # Save the current bed image
                current_bed_path = "/home/mks/opencvtest/currentbed.jpg"
                cv2.imwrite(current_bed_path, frame)
                self.gcode.respond_info(f"Current bed image captured and saved to {current_bed_path}")
            else:
                self.gcode.respond_info("Error: Failed to decode image")
        
        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")

    def cmd_check_object_on_bed(self, gcmd):
        try:
            # Load the empty bed and current bed images
            empty_bed_path_140 = "/home/mks/opencvtest/emptybed140.jpg"
            empty_bed_path_250 = "/home/mks/opencvtest/emptybed250.jpg"
            current_bed_path = "/home/mks/opencvtest/currentbed.jpg"

            empty_bed_140 = cv2.imread(empty_bed_path_140)
            empty_bed_250 = cv2.imread(empty_bed_path_250)
            current_bed = cv2.imread(current_bed_path)

            if empty_bed_140 is None or empty_bed_250 is None or current_bed is None:
                self.gcode.respond_info("Error: Empty or current bed image not found.")
                return

            # Convert images to grayscale
            empty_bed_gray_140 = cv2.cvtColor(empty_bed_140, cv2.COLOR_BGR2GRAY)
            empty_bed_gray_250 = cv2.cvtColor(empty_bed_250, cv2.COLOR_BGR2GRAY)
            current_bed_gray = cv2.cvtColor(current_bed, cv2.COLOR_BGR2GRAY)

            # Function to check for an object by comparing images
            def check_for_object(empty_bed_gray, current_bed_gray):
                diff = cv2.absdiff(empty_bed_gray, current_bed_gray)
                _, thresh = cv2.threshold(diff, 50, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                min_contour_area = 50  # Adjust as needed
                valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]
                return len(valid_contours) == 0  # Returns True if images match (no object detected)

            # Step 1: Check empty_bed_140 against current_bed
            matches_140 = check_for_object(empty_bed_gray_140, current_bed_gray)

            if matches_140:
                self.gcode.respond_info("Match found with emptybed140. Proceeding with print.")
                return  # Allow printing

            # Step 2: Check empty_bed_250 against current_bed (only if 140 did not match)
            matches_250 = check_for_object(empty_bed_gray_250, current_bed_gray)

            if matches_250:
                self.gcode.respond_info("Match found with emptybed250. Proceeding with print.")
                return  # Allow printing

            # If neither 140 nor 250 matched, cancel the print
            self.gcode.respond_info(f"Object detected on the bed! Canceling print job...")
            self.gcode.run_script_from_command("CANCEL_PRINT")

        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")

def load_config(config):
    return cv2_bed_object_detect(config)