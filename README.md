#  Face Scanner + Emotion Detector

## Overview
**Face Scanner + Emotion Detector** is a Python-based web application that detects human facial expressions in real time using your webcam.  

Users can:
- Scan faces live through their camera  
- Detect and display emotions such as happy, sad, angry, surprised, fear, disgust, and neutral  
- Save snapshots of detected faces along with the detected emotion  
- View, manage, and delete captured snapshots in a gallery  

This project uses **DeepFace** for emotion detection and **Flask** for the web interface.


##  Features

- **Real-time Face Detection:** Uses your webcam to detect faces live.  
- **Emotion Analysis:** Predicts dominant emotion and scores for each frame.  
- **Snapshot Capture:** Save detected faces as images with emotion labels and timestamps.  
- **Gallery View:** Browse captured snapshots with details.  
- **Delete Functionality:** Remove unwanted captures directly from the gallery.  
- **Robust Logging:** Each captured face and its emotion are stored in a CSV log for future reference.  

---

## Supported Emotions

The emotion detector can recognize the following emotions:  

- Happy  
- Sad  
- Angry  
- Surprised  
- Fear  
- Disgust  
- Neutral  

---

##  Technologies Used

**Programming Language:** Python 3.8+  

**Libraries & Tools:**
- [Flask] – Web framework  
- [OpenCV] – Real-time image capture and processing  
- [DeepFace] – Facial emotion recognition  
- [Pandas] – CSV logging  
- HTML/CSS – Frontend for live display and gallery  



# Project Structure
  ```test
  Face-Scanner-Emotion-Detector/
  │
  ├── static/
  │   ├── captures/           # Saved face snapshots
  │   └── style.css            # Styles for frontend
  │
  ├── templates/
  │   ├── index.html           # Main scanner page
  │   └── gallery.html         # Gallery view
  │
  ├── .gitignore
  ├── app.py                  # Main Flask application
  └── requirements.txt         # Python dependencies
```

# Installation
## Clone the repository
git clone https://github.com/Micheal-Onyinye/Face-Scanner-Emotion-Detector.git
cd Face-Scanner-Emotion-Detector
## Install dependencies

It is recommended to use a virtual environment:

python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# How to Run

Start the Flask application:

python app.py

Open your browser and go to: http://127.0.0.1:5000/

Point your camera at a face. The detected emotion will be displayed live.

Click "Save Snapshot" to store the face and emotion data.

Visit the Gallery page to view, manage, or delete captured snapshots.

# Gallery Management

Each saved snapshot shows:

Detected emotion

Timestamp

You can delete any snapshot; the log CSV will automatically update.

# How It Works

The webcam captures live frames.

DeepFace.analyze() analyzes faces in each frame for emotion.

Detected faces are highlighted with bounding boxes, and emotion scores are displayed.

Press Save Snapshot to extract and save the face along with the emotion.

All saved images and details are logged in logs/events.csv.
