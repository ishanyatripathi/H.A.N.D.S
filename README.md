![image](https://github.com/user-attachments/assets/f118ca21-41cb-49bf-b7f4-428efd2e8f79)

🤖 H.A.N.D.S. Human Actuated Navigation & Dynamic System

H.A.N.D.S. is a real-time gesture-based control system built with MediaPipe and PyAutoGUI.
It transforms your webcam into an intelligent input device that lets you control your computer
using hand movements no hardware or wearable needed.

✨ Features

🖱️ Mouse Control – Move your cursor using your index finger.
🖱️ Click Detection – Pinch (thumb + index) to trigger mouse clicks.
🔉 Volume Control Mode – Adjust system volume using your left hand.
📜 Scrolling – Scroll pages vertically with the left index finger.
🔍 Zooming – Pinch gesture between left and right hands to zoom in/out.
🎵 Swipe Control – Swipe right index finger across a center line to change songs.
🧠 Smooth Tracking – Movement smoothing with tolerance tuning.
🖲️ Toggle Button – On-screen switch to toggle volume mode.
📏 Visual Feedback – FPS counter, gesture hints, and center line for swipes.

🧰 Tech Stack

- Python
- MediaPipe
- PyAutoGUI
- PyCaw
- OpenCV

🖥️ How It Works

1. Open the app webcam activates.
2. A toggle button appears on screen:
   - Green = Normal Mode
   - Red = Volume Mode
3. Use hand gestures to control the system as follows:
   - Cursor: Right index finger
   - Click: Thumb + Index pinch
   - Scroll: Left index up/down
   - Zoom: Pinch between both hands
   - Volume: Toggle to volume mode and use left hand
   - Swipe: Right index crosses center line to skip tracks

🧪 Requirements

Install dependencies:

pip install opencv-python mediapipe pyautogui comtypes pycaw numpy

🚀 Getting Started

1. Clone the repo:
   git clone https://github.com/ishanyatripathi/H.A.N.D.S
   cd H.A.N.D.S

2. Run the program:
   python main.py
   
### 📄 License
This project is licensed under the [MIT License](./LICENSE).
You are free to use, modify, and distribute this software with proper attribution.
