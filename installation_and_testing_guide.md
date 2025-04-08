# Installation and Testing Guide

## Installation

### Method 1: Install from source

```bash
# Clone the repository
git clone https://github.com/yourusername/eye-mouse-controller
cd eye-mouse-controller

# Install in development mode
pip install -e .
```

### Method 2: Install using pip

```bash
pip install eye-mouse-controller
```

## Running the Application

After installation, run the application with:

```bash
# If installed with pip or in development mode
eye-mouse

# Or run the main module directly
python -m eye_mouse_controller.main
```

## Testing

Run the test suite:

```bash
# Run all tests
python -m unittest discover

# Run a specific test file
python -m unittest tests.test_eye_tracker
python -m unittest tests.test_gesture_controller
python -m unittest tests.test_mouse_controller

# Run a specific test case
python -m unittest tests.test_eye_tracker.TestEyeTracker.test_calculate_distance
```

## Development

To set up the development environment:

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
flake8 eye_mouse_controller tests

# Generate documentation
cd docs
make html
```