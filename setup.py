from setuptools import setup, find_packages

setup(
    name="kalEmc",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "opencv-python>=4.7.0",
        "mediapipe>=0.10.0",
        "pyautogui>=0.9.54",
        "pynput>=1.7.6",
        "SpeechRecognition>=3.10.0",
        "PyAudio>=0.2.13",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "eye-mouse=KalEmc.main:main",
        ],
    },
    author="Eye Mouse Assistant Team",
    author_email="example@example.com",
    description="Control your mouse pointer with eye movement and blinking gestures",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
        "Topic :: Utilities",
        "Topic :: Desktop Environment :: Accessibility",
    ],
    python_requires=">=3.8",
)