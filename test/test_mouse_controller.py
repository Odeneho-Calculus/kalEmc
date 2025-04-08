import unittest
from unittest.mock import patch, MagicMock
from eye_mouse_controller.mouse_controller import MouseController

class TestMouseController(unittest.TestCase):
    def setUp(self):
        # Patch pyautogui to avoid actual mouse movements during tests
        self.pyautogui_patcher = patch('pyautogui.size', return_value=(1920, 1080))
        self.mock_size = self.pyautogui_patcher.start()
        
        # Create the mouse controller
        self.mouse_controller = MouseController()
    
    def tearDown(self):
        # Stop patchers
        self.pyautogui_patcher.stop()
    
    def test_get_screen_size(self):
        # Test screen size retrieval
        width, height = self.mouse_controller.get_screen_size()
        self.assertEqual(width, 1920)
        self.assertEqual(height, 1080)
    
    @patch('pyautogui.position')
    def test_get_current_position(self, mock_position):
        # Configure mock
        mock_position.return_value = (500, 400)
        
        # Test position retrieval
        x, y = self.mouse_controller.get_current_position()
        self.assertEqual(x, 500)
        self.assertEqual(y, 400)
    
    @patch('pyautogui.moveTo')
    def test_move_to(self, mock_move_to):
        # Test absolute movement
        self.mouse_controller.move_to(800, 600)
        mock_move_to.assert_called_once_with(800, 600)
        
        # Test boundary handling
        mock_move_to.reset_mock()
        self.mouse_controller.move_to(2000, 1200)  # Beyond screen bounds
        mock_move_to.assert_called_once_with(1920, 1080)  # Should be clamped
        
        # Test error handling
        mock_move_to.reset_mock()
        mock_move_to.side_effect = Exception("Test exception")
        result = self.mouse_controller.move_to(500, 500)
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.moveRel')
    def test_move_relative(self, mock_move_rel):
        # Test relative movement
        self.mouse_controller.move_relative(10, -20)
        mock_move_rel.assert_called_once_with(10, -20)
        
        # Test error handling
        mock_move_rel.reset_mock()
        mock_move_rel.side_effect = Exception("Test exception")
        result = self.mouse_controller.move_relative(5, 5)
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.click')
    def test_left_click(self, mock_click):
        # Test left click
        self.mouse_controller.left_click()
        mock_click.assert_called_once()
        
        # Test error handling
        mock_click.reset_mock()
        mock_click.side_effect = Exception("Test exception")
        result = self.mouse_controller.left_click()
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.rightClick')
    def test_right_click(self, mock_right_click):
        # Test right click
        self.mouse_controller.right_click()
        mock_right_click.assert_called_once()
        
        # Test error handling
        mock_right_click.reset_mock()
        mock_right_click.side_effect = Exception("Test exception")
        result = self.mouse_controller.right_click()
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.doubleClick')
    def test_double_click(self, mock_double_click):
        # Test double click
        self.mouse_controller.double_click()
        mock_double_click.assert_called_once()
        
        # Test error handling
        mock_double_click.reset_mock()
        mock_double_click.side_effect = Exception("Test exception")
        result = self.mouse_controller.double_click()
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.scroll')
    def test_scroll(self, mock_scroll):
        # Test scrolling
        self.mouse_controller.scroll(5)  # Scroll up
        mock_scroll.assert_called_once_with(5)
        
        mock_scroll.reset_mock()
        self.mouse_controller.scroll(-10)  # Scroll down
        mock_scroll.assert_called_once_with(-10)
        
        # Test error handling
        mock_scroll.reset_mock()
        mock_scroll.side_effect = Exception("Test exception")
        result = self.mouse_controller.scroll(3)
        self.assertFalse(result)  # Should return False on error
    
    @patch('pyautogui.dragTo')
    def test_drag_to(self, mock_drag_to):
        # Test dragging
        self.mouse_controller.drag_to(300, 200)
        mock_drag_to.assert_called_once_with(300, 200, button='left')
        
        mock_drag_to.reset_mock()
        self.mouse_controller.drag_to(500, 400, button='right')
        mock_drag_to.assert_called_once_with(500, 400, button='right')
        
        # Test error handling
        mock_drag_to.reset_mock()
        mock_drag_to.side_effect = Exception("Test exception")
        result = self.mouse_controller.drag_to(100, 100)
        self.assertFalse(result)  # Should return False on error

if __name__ == '__main__':
    unittest.main()