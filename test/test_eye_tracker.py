import unittest
import cv2
import numpy as np
from unittest.mock import MagicMock, patch
from eye_mouse_controller.eye_tracker import EyeTracker

class TestEyeTracker(unittest.TestCase):
    def setUp(self):
        # Mock the camera and face mesh
        with patch('cv2.VideoCapture') as mock_cap:
            with patch('mediapipe.solutions.face_mesh.FaceMesh') as mock_face_mesh:
                # Configure mocks
                mock_cap.return_value.isOpened.return_value = True
                mock_cap.return_value.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
                
                # Create the eye tracker
                self.eye_tracker = EyeTracker(camera_id=0)
                
                # Replace the actual face mesh with a mock
                self.eye_tracker.face_mesh = MagicMock()

    def test_initialize_camera(self):
        # Test successful camera initialization
        self.assertTrue(self.eye_tracker.initialize_camera())
        
        # Test failed camera initialization
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap.return_value.isOpened.return_value = False
            self.assertFalse(self.eye_tracker.initialize_camera())

    def test_capture_frame(self):
        # Test successful frame capture
        frame = self.eye_tracker.capture_frame()
        self.assertIsNotNone(frame)
        
        # Test failed frame capture
        self.eye_tracker.cap.read.return_value = (False, None)
        frame = self.eye_tracker.capture_frame()
        self.assertIsNone(frame)

    def test_detect_eyes_no_face(self):
        # Test when no face is detected
        self.eye_tracker.face_mesh.process.return_value.multi_face_landmarks = None
        result = self.eye_tracker.detect_eyes(np.zeros((480, 640, 3), dtype=np.uint8))
        self.assertIsNone(result)

    def test_calculate_distance(self):
        point1 = (0, 0, 0)
        point2 = (3, 4, 0)
        distance = self.eye_tracker._calculate_distance(point1, point2)
        self.assertEqual(distance, 5.0)  # Pythagoras theorem: 3^2 + 4^2 = 5^2

    def test_calculate_eye_center(self):
        eye_points = [(0, 0, 0), (2, 0, 0), (0, 2, 0), (2, 2, 0)]
        center = self.eye_tracker._calculate_eye_center(eye_points)
        self.assertEqual(center, (1, 1))

    def test_check_blink_state(self):
        current_time = 100.0
        eye_state = {'closed': False, 'closed_time': 0, 'last_blink': 0}
        
        # Test eye not closed
        blink_info = self.eye_tracker._check_blink_state(0.05, eye_state, current_time, threshold=0.018)
        self.assertFalse(blink_info['is_closed'])
        self.assertFalse(blink_info['blink_detected'])
        
        # Test eye just closed
        blink_info = self.eye_tracker._check_blink_state(0.01, eye_state, current_time, threshold=0.018)
        self.assertTrue(blink_info['is_closed'])
        self.assertFalse(blink_info['blink_detected'])
        self.assertTrue(eye_state['closed'])
        self.assertEqual(eye_state['closed_time'], current_time)
        
        # Test eye opened after being closed (completed blink)
        eye_state = {'closed': True, 'closed_time': current_time - 0.2, 'last_blink': 0}
        blink_info = self.eye_tracker._check_blink_state(0.05, eye_state, current_time, threshold=0.018)
        self.assertFalse(blink_info['is_closed'])
        self.assertTrue(blink_info['blink_detected'])
        self.assertFalse(eye_state['closed'])
        self.assertEqual(eye_state['last_blink'], current_time)
        
        # Test long blink
        eye_state = {'closed': True, 'closed_time': current_time - 1.5, 'last_blink': 0}
        blink_info = self.eye_tracker._check_blink_state(0.05, eye_state, current_time, threshold=0.018)
        self.assertFalse(blink_info['is_closed'])
        self.assertTrue(blink_info['blink_detected'])
        self.assertTrue(blink_info['long_blink'])
        
        # Test double blink
        eye_state = {'closed': True, 'closed_time': current_time - 0.2, 'last_blink': current_time - 0.3}
        blink_info = self.eye_tracker._check_blink_state(0.05, eye_state, current_time, threshold=0.018)
        self.assertFalse(blink_info['is_closed'])
        self.assertTrue(blink_info['blink_detected'])
        self.assertTrue(blink_info['double_blink'])

    def tearDown(self):
        self.eye_tracker.release()

if __name__ == '__main__':
    unittest.main()