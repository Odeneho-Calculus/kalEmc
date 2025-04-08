import cv2
import mediapipe as mp
import numpy as np
import logging
import time

logger = logging.getLogger(__name__)

class EyeTracker:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices for eyes
        # These indices are specific to MediaPipe face mesh
        self.LEFT_EYE_INDICES = [362, 385, 387, 263, 373, 380]  # Left eye landmarks
        self.RIGHT_EYE_INDICES = [33, 160, 158, 133, 153, 144]  # Right eye landmarks
        
        # For blink detection
        self.LEFT_EYE_VERTICAL = [385, 380]  # Top and bottom landmarks
        self.RIGHT_EYE_VERTICAL = [160, 144]  # Top and bottom landmarks
        
        # For pupil tracking (iris landmarks)
        self.LEFT_IRIS = [474, 475, 476, 477]  # Left iris landmarks
        self.RIGHT_IRIS = [469, 470, 471, 472]  # Right iris landmarks
        
        # Blink state tracking
        self.left_eye_state = {'closed': False, 'closed_time': 0, 'last_blink': 0}
        self.right_eye_state = {'closed': False, 'closed_time': 0, 'last_blink': 0}
        
        # Frame dimensions
        self.frame_width = 0
        self.frame_height = 0
        
        # Initialize camera
        self.initialize_camera()
        
    def initialize_camera(self):
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                logger.error(f"Cannot open camera {self.camera_id}")
                return False
                
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual frame dimensions
            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            logger.info(f"Camera {self.camera_id} initialized successfully with resolution {self.frame_width}x{self.frame_height}")
            return True
        except Exception as e:
            logger.error(f"Error initializing camera: {e}")
            return False
    
    def capture_frame(self):
        if self.cap is None or not self.cap.isOpened():
            if not self.initialize_camera():
                return None
                
        ret, frame = self.cap.read()
        if not ret:
            logger.error("Failed to capture frame")
            return None
            
        # Flip the frame horizontally for a selfie-view display
        frame = cv2.flip(frame, 1)
        return frame
    
    def detect_eyes(self, frame):
        if frame is None:
            return None
            
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process the frame to detect face landmarks
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None
            
        face_landmarks = results.multi_face_landmarks[0]
        
        # Extract eye landmarks
        h, w, _ = frame.shape
        landmark_points = []
        
        for idx, landmark in enumerate(face_landmarks.landmark):
            x, y = int(landmark.x * w), int(landmark.y * h)
            landmark_points.append((x, y, landmark.z))
        
        # Get eye landmarks
        left_eye = [landmark_points[i] for i in self.LEFT_EYE_INDICES]
        right_eye = [landmark_points[i] for i in self.RIGHT_EYE_INDICES]
        
        # Get iris landmarks for more accurate pupil tracking
        left_iris = [landmark_points[i] for i in self.LEFT_IRIS] if len(landmark_points) > 478 else None
        right_iris = [landmark_points[i] for i in self.RIGHT_IRIS] if len(landmark_points) > 473 else None
        
        # Calculate eye aspect ratio for blink detection
        left_eye_top = landmark_points[self.LEFT_EYE_VERTICAL[0]]
        left_eye_bottom = landmark_points[self.LEFT_EYE_VERTICAL[1]]
        left_eye_height = self._calculate_distance(left_eye_top, left_eye_bottom)
        
        right_eye_top = landmark_points[self.RIGHT_EYE_VERTICAL[0]]
        right_eye_bottom = landmark_points[self.RIGHT_EYE_VERTICAL[1]]
        right_eye_height = self._calculate_distance(right_eye_top, right_eye_bottom)
        
        # Check blink state
        current_time = time.time()
        left_blink_info = self._check_blink_state(left_eye_height, self.left_eye_state, current_time, threshold=0.018)
        right_blink_info = self._check_blink_state(right_eye_height, self.right_eye_state, current_time, threshold=0.018)
        
        # Calculate eye centers
        left_eye_center = self._calculate_eye_center(left_eye)
        right_eye_center = self._calculate_eye_center(right_eye)
        
        # Calculate pupil positions - prefer iris landmarks if available
        if left_iris and right_iris:
            left_pupil = self._calculate_iris_center(left_iris, left_eye)
            right_pupil = self._calculate_iris_center(right_iris, right_eye)
        else:
            # Fallback to darkest point method
            left_pupil = self._detect_pupil(frame, left_eye)
            right_pupil = self._detect_pupil(frame, right_eye)
        
        # Optional: Draw visual debug indicators on frame
        debug_frame = self._draw_debug_indicators(frame.copy(), left_eye, right_eye, 
                                                 left_pupil, right_pupil, 
                                                 left_blink_info, right_blink_info)
        # Show debug frame
        # cv2.imshow("Eye Tracking Debug", debug_frame)
        # cv2.waitKey(1)
        
        # Calculate gaze direction
        gaze_info = {
            'left_eye_center': left_eye_center,
            'right_eye_center': right_eye_center,
            'left_pupil': left_pupil,
            'right_pupil': right_pupil,
            'left_blink': left_blink_info,
            'right_blink': right_blink_info
        }
        
        return gaze_info
    
    def _calculate_distance(self, point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2 + (point1[2] - point2[2])**2)
    
    def _calculate_eye_center(self, eye_points):
        x_coords = [p[0] for p in eye_points]
        y_coords = [p[1] for p in eye_points]
        return (int(np.mean(x_coords)), int(np.mean(y_coords)))
    
    def _calculate_iris_center(self, iris_points, eye_points):
        """Calculate iris center and relative position within eye region"""
        iris_center_x = np.mean([p[0] for p in iris_points])
        iris_center_y = np.mean([p[1] for p in iris_points])
        
        # Calculate eye region boundaries
        min_x = min(p[0] for p in eye_points)
        max_x = max(p[0] for p in eye_points)
        min_y = min(p[1] for p in eye_points)
        max_y = max(p[1] for p in eye_points)
        
        # Calculate relative position (normalized between -1 and 1)
        eye_width = max_x - min_x
        eye_height = max_y - min_y
        
        if eye_width == 0 or eye_height == 0:
            relative_x = 0
            relative_y = 0
        else:
            eye_center_x = (min_x + max_x) / 2
            eye_center_y = (min_y + max_y) / 2
            
            relative_x = 2 * (iris_center_x - eye_center_x) / eye_width
            relative_y = 2 * (iris_center_y - eye_center_y) / eye_height
        
        # Amplify to make movements more pronounced
        relative_x *= 2.0
        relative_y *= 2.0
        
        return {
            'position': (int(iris_center_x), int(iris_center_y)),
            'relative_x': relative_x,
            'relative_y': relative_y
        }
    
    def _detect_pupil(self, frame, eye_points):
        """Detect pupil using the darkest point in the eye region"""
        # Create a mask for the eye region
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        eye_points_2d = [(p[0], p[1]) for p in eye_points]
        eye_points_2d = np.array(eye_points_2d, dtype=np.int32)
        cv2.fillPoly(mask, [eye_points_2d], 255)
        
        # Extract the eye region
        eye_roi = cv2.bitwise_and(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), mask=mask)
        
        # Apply GaussianBlur to reduce noise
        eye_roi = cv2.GaussianBlur(eye_roi, (7, 7), 0)
        
        # Find the darkest point in the eye region (approximation of pupil)
        min_val, _, min_loc, _ = cv2.minMaxLoc(eye_roi, mask=mask)
        
        # Calculate eye boundaries
        min_x = min(p[0] for p in eye_points)
        max_x = max(p[0] for p in eye_points)
        min_y = min(p[1] for p in eye_points)
        max_y = max(p[1] for p in eye_points)
        
        # Calculate eye center
        eye_center_x = (min_x + max_x) / 2
        eye_center_y = (min_y + max_y) / 2
        
        # Calculate relative positions
        eye_width = max_x - min_x
        eye_height = max_y - min_y
        
        if eye_width == 0 or eye_height == 0:
            relative_x = 0
            relative_y = 0
        else:
            relative_x = 2 * (min_loc[0] - eye_center_x) / eye_width
            relative_y = 2 * (min_loc[1] - eye_center_y) / eye_height
            
        # Amplify to make movements more pronounced
        relative_x *= 2.0
        relative_y *= 2.0
        
        return {
            'position': min_loc,
            'relative_x': relative_x,
            'relative_y': relative_y
        }
    
    def _check_blink_state(self, eye_height, eye_state, current_time, threshold=0.018):
        """Check if the eye is blinking and what type of blink it is"""
        # Determine if eye is closed based on height threshold
        is_closed = eye_height < threshold
        
        # Update state tracking
        blink_info = {
            'is_closed': is_closed,
            'duration': 0,
            'blink_detected': False,
            'long_blink': False,
            'double_blink': False
        }
        
        if is_closed and not eye_state['closed']:
            # Eye just closed
            eye_state['closed'] = True
            eye_state['closed_time'] = current_time
        elif not is_closed and eye_state['closed']:
            # Eye just opened - completed a blink
            eye_state['closed'] = False
            blink_duration = current_time - eye_state['closed_time']
            
            # Check if it's a long blink (≥1 second)
            if blink_duration >= 1.0:
                blink_info['long_blink'] = True
                logger.debug(f"Long blink detected: {blink_duration:.2f}s")
            
            # Check if it's a double blink (two blinks within 0.5 seconds)
            if current_time - eye_state['last_blink'] < 0.5:
                blink_info['double_blink'] = True
                logger.debug("Double blink detected")
            
            eye_state['last_blink'] = current_time
            blink_info['blink_detected'] = True
            blink_info['duration'] = blink_duration
        
        # If still closed, update the current duration
        if is_closed:
            blink_info['duration'] = current_time - eye_state['closed_time']
            
        return blink_info
    
    def _draw_debug_indicators(self, frame, left_eye, right_eye, left_pupil, right_pupil, left_blink, right_blink):
        """Draw debug indicators on the frame for visualization"""
        # Draw eye regions
        left_eye_points = np.array([(p[0], p[1]) for p in left_eye], dtype=np.int32)
        right_eye_points = np.array([(p[0], p[1]) for p in right_eye], dtype=np.int32)
        
        cv2.polylines(frame, [left_eye_points], True, (0, 255, 0), 1)
        cv2.polylines(frame, [right_eye_points], True, (0, 255, 0), 1)
        
        # Draw pupils
        if left_pupil:
            cv2.circle(frame, left_pupil['position'], 3, (0, 0, 255), -1)
        if right_pupil:
            cv2.circle(frame, right_pupil['position'], 3, (0, 0, 255), -1)
        
        # Add gaze direction text
        if left_pupil and right_pupil:
            gaze_text = f"Gaze: L({left_pupil['relative_x']:.2f}, {left_pupil['relative_y']:.2f}), " \
                        f"R({right_pupil['relative_x']:.2f}, {right_pupil['relative_y']:.2f})"
            cv2.putText(frame, gaze_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Add blink status
        left_status = "Closed" if left_blink['is_closed'] else "Open"
        right_status = "Closed" if right_blink['is_closed'] else "Open"
        
        cv2.putText(frame, f"Left: {left_status}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(frame, f"Right: {right_status}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def release(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        self.face_mesh.close()
        cv2.destroyAllWindows()
        logger.info("Eye tracker resources released")