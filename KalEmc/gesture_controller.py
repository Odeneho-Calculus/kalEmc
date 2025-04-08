import logging
import time
import numpy as np

logger = logging.getLogger(__name__)

class GestureController:
    def __init__(self, mouse_controller, sensitivity=20, smoothing=0.5):
        self.mouse_controller = mouse_controller
        self.sensitivity = sensitivity  # Increased sensitivity
        self.smoothing = smoothing      # Reduced smoothing for more responsive movement
        
        # Previous eye positions for smoothing
        self.prev_left_pupil = None
        self.prev_right_pupil = None
        
        # Blink tracking
        self.last_blink_time = 0
        self.blink_count = 0
        self.double_blink_threshold = 0.5  # Time window for double blink detection
        
        # Screen dimensions
        self.screen_width, self.screen_height = self.mouse_controller.get_screen_size()
        
        # Default calibration values - adjusted to be more sensitive
        self.center_x = 0
        self.center_y = 0
        self.range_x = 0.5  # Reduced range means smaller eye movements create larger cursor movements
        self.range_y = 0.5
        
        # Debug info
        self.last_norm_x = 0
        self.last_norm_y = 0
        
        logger.info("Gesture controller initialized")
        
    def calibrate(self, center_x=0, center_y=0, range_x=0.5, range_y=0.5):
        """Update calibration parameters for mapping eye positions to screen coordinates"""
        self.center_x = center_x
        self.center_y = center_y
        self.range_x = range_x
        self.range_y = range_y
        logger.info(f"Calibration updated: center=({center_x}, {center_y}), range=({range_x}, {range_y})")
        
    def process_eye_data(self, eye_data):
        """Process eye tracking data and convert to mouse actions"""
        if not eye_data:
            return
            
        # Process blinks first
        self._process_blinks(eye_data)
        
        # Process gaze for mouse movement
        self._process_gaze(eye_data)
        
    def _process_blinks(self, eye_data):
        """Handle blink-based mouse events"""
        left_blink = eye_data.get('left_blink', {})
        right_blink = eye_data.get('right_blink', {})
        current_time = time.time()
        
        # Handle left eye long blink (right click)
        if left_blink.get('long_blink', False):
            logger.debug("Long blink detected - Right click")
            self.mouse_controller.right_click()
            time.sleep(0.5)  # Prevent immediate re-detection
            
        # Handle left eye double blink (double click)
        elif left_blink.get('double_blink', False):
            logger.debug("Double blink detected - Double click")
            self.mouse_controller.double_click()
            time.sleep(0.5)  # Prevent immediate re-detection
            
        # Handle single blink (left click)
        elif left_blink.get('blink_detected', False) and not right_blink.get('blink_detected', False):
            # Only consider it a single click if it's not part of a double click sequence
            if current_time - self.last_blink_time > self.double_blink_threshold:
                logger.debug("Single blink detected - Left click")
                self.mouse_controller.left_click()
                
            self.last_blink_time = current_time
            
        # Handle left wink (scroll up)
        if not left_blink.get('is_closed', False) and right_blink.get('is_closed', False):
            logger.debug("Right wink detected - Scroll down")
            self.mouse_controller.scroll(-2)  # Negative values scroll down
            
        # Handle right wink (scroll down)
        elif left_blink.get('is_closed', False) and not right_blink.get('is_closed', False):
            logger.debug("Left wink detected - Scroll up")
            self.mouse_controller.scroll(2)  # Positive values scroll up
            
    def _process_gaze(self, eye_data):
        """Handle gaze-based mouse movement"""
        # Average the positions from both eyes for more stability
        left_pupil = eye_data.get('left_pupil', {})
        right_pupil = eye_data.get('right_pupil', {})
        
        if not left_pupil or not right_pupil:
            return
            
        # Get relative positions
        left_x = left_pupil.get('relative_x', 0)
        left_y = left_pupil.get('relative_y', 0)
        right_x = right_pupil.get('relative_x', 0)
        right_y = right_pupil.get('relative_y', 0)
        
        # Average the two eyes with some base amplification
        avg_x = (left_x + right_x) * 1.5
        avg_y = (left_y + right_y) * 1.5
        
        # Apply smoothing if we have previous positions
        if self.prev_left_pupil is not None and self.prev_right_pupil is not None:
            avg_x = avg_x * (1 - self.smoothing) + ((self.prev_left_pupil.get('relative_x', 0) + 
                                                     self.prev_right_pupil.get('relative_x', 0)) * 1.5) * self.smoothing
            avg_y = avg_y * (1 - self.smoothing) + ((self.prev_left_pupil.get('relative_y', 0) + 
                                                     self.prev_right_pupil.get('relative_y', 0)) * 1.5) * self.smoothing
        
        # Map to screen coordinates
        norm_x = (avg_x - self.center_x) / self.range_x
        norm_y = (avg_y - self.center_y) / self.range_y
        
        # Log significant changes in gaze direction for debugging
        if abs(norm_x - self.last_norm_x) > 0.1 or abs(norm_y - self.last_norm_y) > 0.1:
            logger.debug(f"Gaze direction: x={norm_x:.2f}, y={norm_y:.2f}")
            self.last_norm_x = norm_x
            self.last_norm_y = norm_y
        
        # Apply sensitivity and calculate new position
        # Convert to absolute screen coordinates
        target_x = int((norm_x * self.sensitivity * self.screen_width/20) + (self.screen_width / 2))
        target_y = int((norm_y * self.sensitivity * self.screen_height/20) + (self.screen_height / 2))
        
        # Ensure within screen bounds
        target_x = max(0, min(self.screen_width, target_x))
        target_y = max(0, min(self.screen_height, target_y))
        
        # Move mouse pointer if movement is significant enough
        # Reduced threshold to make movement more responsive
        if abs(norm_x) > 0.02 or abs(norm_y) > 0.02:
            logger.debug(f"Moving mouse to: ({target_x}, {target_y})")
            self.mouse_controller.move_to(target_x, target_y)
        
        # Store for next smoothing calculation
        self.prev_left_pupil = left_pupil
        self.prev_right_pupil = right_pupil