import pyautogui
import logging

logger = logging.getLogger(__name__)

# Configure PyAutoGUI to be safer
pyautogui.FAILSAFE = True  # Move mouse to upper-left to abort

class MouseController:
    def __init__(self):
        # Get screen dimensions
        self.screen_width, self.screen_height = pyautogui.size()
        self.safe_margin = 50  # Define a safe margin from the screen edges
        logger.info(f"Screen dimensions: {self.screen_width}x{self.screen_height}")

    def get_screen_size(self):
        """Return the screen dimensions"""
        return self.screen_width, self.screen_height

    def get_current_position(self):
        """Get current mouse position"""
        return pyautogui.position()

    def move_to(self, x, y):
        """Move mouse to absolute coordinates with custom fail-safe"""
        try:
            # Ensure coordinates are within screen bounds and avoid corners
            if (self.safe_margin < x < self.screen_width - self.safe_margin and
                self.safe_margin < y < self.screen_height - self.safe_margin):
                pyautogui.moveTo(x, y)
                return True
            else:
                logger.warning("Mouse movement to corner prevented by custom fail-safe")
                return False
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
            return False

    def move_relative(self, dx, dy):
        """Move mouse by relative amount with custom fail-safe"""
        try:
            current_x, current_y = self.get_current_position()
            new_x = current_x + dx
            new_y = current_y + dy

            # Ensure new position is within screen bounds and avoid corners
            if (self.safe_margin < new_x < self.screen_width - self.safe_margin and
                self.safe_margin < new_y < self.screen_height - self.safe_margin):
                pyautogui.moveRel(dx, dy)
                return True
            else:
                logger.warning("Mouse movement to corner prevented by custom fail-safe")
                return False
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
            return False

    def left_click(self):
        """Perform a left mouse button click"""
        try:
            pyautogui.click()
            logger.debug("Left click performed")
            return True
        except Exception as e:
            logger.error(f"Error performing left click: {e}")
            return False

    def right_click(self):
        """Perform a right mouse button click"""
        try:
            pyautogui.rightClick()
            logger.debug("Right click performed")
            return True
        except Exception as e:
            logger.error(f"Error performing right click: {e}")
            return False

    def double_click(self):
        """Perform a double click"""
        try:
            pyautogui.doubleClick()
            logger.debug("Double click performed")
            return True
        except Exception as e:
            logger.error(f"Error performing double click: {e}")
            return False

    def scroll(self, amount):
        """Scroll up (positive) or down (negative)"""
        try:
            pyautogui.scroll(amount)
            logger.debug(f"Scrolled by {amount}")
            return True
        except Exception as e:
            logger.error(f"Error scrolling: {e}")
            return False

    def drag_to(self, x, y, button='left'):
        """Drag to position with specified button held"""
        try:
            # Ensure drag destination is within screen bounds and avoid corners
            if (self.safe_margin < x < self.screen_width - self.safe_margin and
                self.safe_margin < y < self.screen_height - self.safe_margin):
                pyautogui.dragTo(x, y, button=button)
                logger.debug(f"Dragged to ({x}, {y}) with {button} button")
                return True
            else:
                logger.warning("Drag to corner prevented by custom fail-safe")
                return False
        except Exception as e:
            logger.error(f"Error dragging: {e}")
            return False
