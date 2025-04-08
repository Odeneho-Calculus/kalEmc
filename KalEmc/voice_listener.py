import threading
import speech_recognition as sr
import logging
import time

logger = logging.getLogger(__name__)

class VoiceListener:
    def __init__(self, wake_word="wake up", sleep_word="go to sleep"):
        self.wake_word = wake_word.lower()
        self.sleep_word = sleep_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.wake_callback = None
        self.sleep_callback = None
        
        # Adjust for ambient noise
        with self.microphone as source:
            logger.info("Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            logger.info("Microphone calibrated")
    
    def set_wake_callback(self, callback):
        self.wake_callback = callback
        
    def set_sleep_callback(self, callback):
        self.sleep_callback = callback
        
    def start_listening(self):
        self.listening = True
        logger.info("Voice listener started")
        
        while self.listening:
            try:
                with self.microphone as source:
                    logger.debug("Listening for commands...")
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                try:
                    text = self.recognizer.recognize_google(audio).lower()
                    logger.debug(f"Recognized: {text}")
                    
                    if self.wake_word in text and self.wake_callback:
                        logger.info(f"Wake word detected: {self.wake_word}")
                        self.wake_callback()
                    elif self.sleep_word in text and self.sleep_callback:
                        logger.info(f"Sleep word detected: {self.sleep_word}")
                        self.sleep_callback()
                        
                except sr.UnknownValueError:
                    # Speech was unintelligible
                    pass
                except sr.RequestError as e:
                    logger.error(f"Could not request results from Google Speech Recognition service; {e}")
                    
            except (sr.WaitTimeoutError, Exception) as e:
                if not isinstance(e, sr.WaitTimeoutError):
                    logger.error(f"Error in voice listener: {e}")
                # Continue listening
                continue
    
    def stop_listening(self):
        logger.info("Stopping voice listener")
        self.listening = False