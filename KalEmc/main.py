import threading
import time
import logging
from KalEmc.voice_listener import VoiceListener
from KalEmc.eye_tracker import EyeTracker
from KalEmc.gesture_controller import GestureController
from KalEmc.mouse_controller import MouseController

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EyeMouseAssistant:
    def __init__(self, wake_word="wake up", sleep_word="go to sleep"):
        logger.info("Initializing Eye Mouse Assistant")
        self.running = False
        self.active = False
        
        # Initialize components
        self.voice_listener = VoiceListener(wake_word, sleep_word)
        self.mouse_controller = MouseController()
        self.eye_tracker = EyeTracker()
        self.gesture_controller = GestureController(self.mouse_controller)
        
        # Register callbacks
        self.voice_listener.set_wake_callback(self.activate)
        self.voice_listener.set_sleep_callback(self.deactivate)
        
    def activate(self):
        logger.info("Activating eye tracking")
        self.active = True
        
    def deactivate(self):
        logger.info("Deactivating eye tracking")
        self.active = False
        
    def start(self):
        self.running = True
        
        # Start voice listener in a separate thread
        voice_thread = threading.Thread(target=self.voice_listener.start_listening)
        voice_thread.daemon = True
        voice_thread.start()
        
        # Main processing loop
        logger.info("Eye Mouse Assistant is running. Say 'wake up' to activate.")
        try:
            while self.running:
                if self.active:
                    # Process eye tracking when active
                    frame = self.eye_tracker.capture_frame()
                    if frame is not None:
                        eye_data = self.eye_tracker.detect_eyes(frame)
                        if eye_data:
                            self.gesture_controller.process_eye_data(eye_data)
                    
                # Sleep to reduce CPU usage
                time.sleep(0.01)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
            
    def stop(self):
        logger.info("Shutting down Eye Mouse Assistant")
        self.running = False
        self.active = False
        self.voice_listener.stop_listening()
        self.eye_tracker.release()

def main():
    assistant = EyeMouseAssistant()
    assistant.start()
            
if __name__ == "__main__":
    main()