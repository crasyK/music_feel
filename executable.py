import cv2
from deepface import DeepFace
import time
import pyttsx3

from func_lib.emotion import get_emotion_duration, get_emotion_last_xseconds
from func_lib.music import SoundCloudPlayer

import cv2
import os
import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

cascade_path = resource_path("cv2/data/haarcascade_frontalface_default.xml")
face_cascade = cv2.CascadeClassifier(cascade_path)


# Load TTS engine
engine = pyttsx3.init()

# Initialize camera
cap = cv2.VideoCapture(0)  # Use 0 for default webcam

# Dictionary to store emotion changes with timestamps
emotion_changes = dict({time.time():'neutral'}) # Start time : emotion -> Duration is start time [a] - start time [a+1]

global start_time
start_time = time.time()

last_time = time.time()

counter_every = 3
last_emotion = 'neutral'
current_song = 'none'

player = SoundCloudPlayer()
playlist_url = input("Please enter the SoundCloud playlist URL: ") # https://soundcloud.com/sc-playlists-de/sets/techno-machinista

player = SoundCloudPlayer()
player.start_playlist(playlist_url)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to RGB for DeepFace
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    try:
        # Analyze emotion (processes at ~3-5 FPS on CPU)    
        
        analysis = DeepFace.analyze(rgb_frame, actions=['emotion'], enforce_detection=False)
        
        # Get dominant emotion
        dominant_emotion = analysis[0]['dominant_emotion'] 
        confidence = analysis[0]['emotion'][dominant_emotion]
        
        last_emotion = list(emotion_changes.values())[-1]
        if dominant_emotion != last_emotion:
                # Record the time of the change
            emotion_changes.update({time.time():dominant_emotion})
        emotion_distribution_overall =  get_emotion_duration(start_time, time.time(),emotion_changes)   
        
        # ---- Notes ----
        # Two Reaction "Types":
        # 1. Reaction to the Song -> Like or Dislike <- Kind of hard to measure 
        # Would mean to differentiate between song related and unrelated emotions and also being able to feed the information to a suitable algorithm
        # 2. Reaction unrelated to music -> Success / Focus / Neutral / Sadness / Anger 
        # This means that if in the last 10/5/3 seconds was a lot of anger, we can assume that the user is angry and we can react to that
        
        # Reaction type 2. is here implemented and is the main focus of this project
        
        # Display results
        cv2.putText(frame, f"{last_emotion}", 
               (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
        if counter_every > 0:
            time.sleep(0.1)
            counter_every -= 0.1
        else:
            counter_every = 3
            # Here is now the Emotion Event section
            # 3 seconds Happy (>80%) -> OMG-Moment
            # 3 seconds Sad (>80%) -> Power Music
            # 3 seconds Angry (>80%) -> Lofi Music
            last_emotion = get_emotion_last_xseconds(5, emotion_changes, start_time)
            print(f"Last Emotion: {last_emotion[0]} with {last_emotion[1]}%")
            if last_emotion[0] == 'happy' and last_emotion[1] > 40.0 and current_song != 'happy':
                current_song = 'happy'
                player.pause()
                print("Detected an OMG moment! Play the trumpets!")
                engine.say("Detected an OMG moment! Play the trumpets!")
                engine.runAndWait()
                player.resume()
                player.interrupt("https://soundcloud.com/manny-fernandez-4856421/trumpet-fanfare-2") 
            elif last_emotion[0] == 'sad' and last_emotion[1] > 80.0 and current_song != 'sad':
                current_song = 'sad'
                player.pause()
                engine.say("Detected a sadness intensivies moment! Initiating Happy Music!")
                engine.runAndWait()
                player.resume()
                player.interrupt("https://soundcloud.com/briona-alex/macarena-bass-boosted-remix") 
            elif last_emotion[0] == 'angry' and last_emotion[1] > 80.0 and current_song != 'angry':
                current_song = 'angry'
                player.pause()
                engine.say("Detected an rage quit! Initiating Lofi Music!")
                engine.runAndWait()
                player.resume()
                player.interrupt("https://soundcloud.com/nymano/solitude?in=user-636346752/sets/lofi-chill") 
            elif last_emotion[0] == 'fear' and last_emotion[1] > 80.0 and current_song != 'fear':
                current_song = 'fear'
                player.pause()
                engine.say("Detected the fear of coding! Initiating giga chad Mindset!")
                engine.runAndWait()
                player.resume()
                player.interrupt("https://soundcloud.com/kashkachefira/eternxlkz-slay-chashkakefira-remake?in=kuhar-ilya/sets/phonk-music-2024-best") 
    
    except Exception as e:
        print(f"Error: {e}")
    # Show live feed
    cv2.imshow("Emotion Recognition", frame)
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()