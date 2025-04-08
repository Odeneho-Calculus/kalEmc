import unittest
from unittest.mock import MagicMock, patch
from eye_mouse_controller.gesture_controller import GestureController

class TestGestureController(unittest.TestCase):
    def setUp(self):
        # Create a mock mouse controller
        self.mock_mouse_controller = MagicMock()
        self.mock_mouse_controller.get_screen_size.return_value = (1920, 1080)
        
        # Create the gesture controller with the mock
        self.gesture_controller = GestureController(self.mock_mouse_controller)

    def test_calibrate(self):
        # Test calibration update
        self.gesture_controller.calibrate(0.1, 0.2, 0.8, 0.7)
        self.assertEqual(self.gesture_controller.center_x, 0.1)
        self.assertEqual(self.gesture_controller.center_y, 0.2)
        self.assertEqual(self.gesture_controller.range_x, 0.8)
        self.assertEqual(self.gesture_controller.range_y, 0.7)

    def test_process_blinks_single_blink(self):
        # Test single blink detection
        eye_data = {
            'left_blink': {
                'is_closed': False,
                'blink_detected': True,
                'long_blink': False,
                'double_blink': False
            },
            'right_blink': {
                'is_closed': False,
                'blink_detected': False
            }
        }
        
        # Ensure enough time has passed since last blink
        self.gesture_controller.last_blink_time = 0
        
        # Process the blink
        self.gesture_controller._process_blinks(eye_data)
        
        # Check that left click was called
        self.mock_mouse_controller.left_click.assert_called_once()

    def test_process_blinks_double_blink(self):
        # Test double blink detection
        eye_data = {
            'left_blink': {
                'is_closed': False,
                'blink_detected': True,
                'long_blink': False,
                'double_blink': True
            },
            'right_blink': {
                'is_closed': False,
                'blink_detected': False
            }
        }
        
        # Process the blink
        self.gesture_controller._process_blinks(eye_data)
        
        # Check that double click was called
        self.mock_mouse_controller.double_click.assert_called_once()

    def test_process_blinks_long_blink(self):
        # Test long blink detection
        eye_data = {
            'left_blink': {
                'is_closed': False,
                'blink_detected': True,
                'long_blink': True,
                'double_blink': False
            },
            'right_blink': {
                'is_closed': False,
                'blink_detected': False
            }
        }
        
        # Process the blink
        self.gesture_controller._process_blinks(eye_data)
        
        # Check that right click was called
        self.mock_mouse_controller.right_click.assert_called_once()

    def test_process_gaze(self):
        # Test gaze processing
        eye_data = {
            'left_pupil': {
                'relative_x': 0.2,
                'relative_y': 0.1
            },
            'right_pupil': {
                'relative_x': 0.3,
                'relative_y': 0.2
            }
        }
        
        # Process the gaze
        self.gesture_controller._process_gaze(eye_data)
        
        # Check that move_to was called with appropriate coordinates
        self.mock_mouse_controller.move_to.assert_called_once()
        
        # Test with smoothing enabled
        self.gesture_controller.prev_left_pupil = {'relative_x': 0.1, 'relative_y': 0.05}
        self.gesture_controller.prev_right_pupil = {'relative_x': 0.2, 'relative_y': 0.15}
        
        # Reset the mock
        self.mock_mouse_controller.move_to.reset_mock()
        
        # Process the gaze again
        self.gesture_controller._process_gaze(eye_data)
        
        # Check that move_to was called with smoothed coordinates
        self.mock_mouse_controller.move_to.assert_called_once()

if __name__ == '__main__':
    unittest.main()