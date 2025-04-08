# Eye Mouse Controller

An intelligent, hands-free mouse pointer control system that uses eye-tracking and blink detection to enable complete mouse control without physical input devices.

## Features

- **Voice Activation**: Activate and deactivate with customizable voice commands
- **Eye Tracking**: Move your mouse pointer by looking at different areas of your screen
- **Blink Commands**:
  - Single blink: Left click
  - Double blink: Double click
  - Long blink (≥1 second): Right click
  - Left wink: Scroll up
  - Right wink: Scroll down
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Complete Project Structure
eye_mouse_controller/
├── setup.py
├── README.md
├── requirements.txt
├── eye_mouse_controller/
│   ├── __init__.py
│   ├── main.py
│   ├── voice_listener.py
│   ├── eye_tracker.py
│   ├── gesture_controller.py
│   ├── mouse_controller.py
│   └── utils.py
└── tests/
    ├── __init__.py
    ├── test_eye_tracker.py
    ├── test_gesture_controller.py
    └── test_mouse_controller.py

## Requirements

- Python 3.8 or higher
- Webcam
- Microphone
- System permissions for camera, microphone, and accessibility features

## Installation

```bash
# Clone the repository
git clone https://github.com/example/eye-mouse-controller
cd eye-mouse-controller

# Install requirements
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Usage

Start the assistant:

```bash
eye-mouse
```

### Voice Commands

- "wake up" - Activate eye tracking
- "Go to sleep" - Deactivate eye tracking

## Configuration

The application will use default settings, but you can customize:

- Sensitivity of eye tracking
- Blink detection thresholds
- Voice activation commands

## Troubleshooting

1. **Camera not detected**: Ensure your webcam is properly connected and you've granted permission to use it
2. **Voice commands not recognized**: Check your microphone setup and ensure it's properly detecting sound
3. **Eye tracking not responsive**: Ensure good lighting conditions and that your eyes are clearly visible

## License

This project is licensed under the MIT License - see the LICENSE file for details.