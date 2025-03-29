import logging
import cv2
import urllib.request
import numpy as np
import os

class Cv2BedObjectDetect:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object("gcode")

        # Register the custom G-code commands
        self.gcode.register_command("CAPTURE_IMAGE_EMPTY_BED", self.cmd_capture_image_empty_bed, desc="Capture an image from the webcam with an empty bed")
        self.gcode.register_command("CAPTURE_IMAGE_CURRENT_BED", self.cmd_capture_image_current_bed, desc="Capture an image from the webcam of the current bed")
        self.gcode.register_command("CHECK_OBJECT_ON_BED", self.cmd_check_object_on_bed, desc="Check if there is an object on the bed by comparing to empty bed")

    def cmd_capture_image_empty_bed(self, gcmd):
        try:
            stream_url = "http://localhost:8080/?action=snapshot"  # Default URL for mjpg-streamer
            resp = urllib.request.urlopen(stream_url)  # Open the URL
            image_array = np.asarray(bytearray(resp.read()), dtype=np.uint8)  # Read and convert to array
            frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)  # Decode image
            
            if frame is not None:
                # Save the empty bed image
                empty_bed_path = "/home/mks/opencvtest/emptybed.jpg"
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
            empty_bed_path = "/home/mks/opencvtest/emptybed.jpg"
            current_bed_path = "/home/mks/opencvtest/currentbed.jpg"

            empty_bed = cv2.imread(empty_bed_path)
            current_bed = cv2.imread(current_bed_path)

            if empty_bed is None or current_bed is None:
                self.gcode.respond_info("Error: Empty or current bed image not found.")
                return

            # Convert both images to grayscale
            empty_bed_gray = cv2.cvtColor(empty_bed, cv2.COLOR_BGR2GRAY)
            current_bed_gray = cv2.cvtColor(current_bed, cv2.COLOR_BGR2GRAY)

            # Compute the absolute difference between the two images
            diff = cv2.absdiff(empty_bed_gray, current_bed_gray)

            # Apply a threshold to the difference image
            _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

            # Find contours in the thresholded image (which highlights the differences)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Minimum area to consider as a valid object (in pixels)
            min_contour_area = 50  # Adjust this value based on your needs

            # Filter contours based on area
            valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_contour_area]

            # If there are valid contours, it means there are objects on the bed
            if len(valid_contours) > 0:
                self.gcode.respond_info(f"Object detected on the bed! Canceling print job...")
                
                # Send the CANCEL_PRINT command to Klipper
                self.gcode.run_script_from_command("CANCEL_PRINT")

            else:
                self.gcode.respond_info("No object detected on the bed. Proceeding with print.")

        except Exception as e:
            self.gcode.respond_info(f"Error: {str(e)}")


def load_config(config):
    return Cv2BedObjectDetect(config)