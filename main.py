import cv2
from deepface import DeepFace
import time
import webbrowser

from dotenv import load_dotenv
from googleapiclient.discovery import build
import webbrowser
import os

def youtube_api_search(api_key, query):
    youtube = build('youtube', 'v3', developerKey=api_key)
    request = youtube.search().list(q=query, part='id,snippet', maxResults=1)
    response = request.execute()
    return response['items'][0]['id']['videoId']

# Load environment variables from .env file
load_dotenv()

# Usage
# Load your YouTube API key from .env file
API_KEY = os.getenv("YOUTUBE_API_KEY")
video_id = youtube_api_search(API_KEY, "Sweet Child O Mine Guns N Roses")
webbrowser.open(f"https://www.youtube.com/watch?v={video_id}&autoplay=1")
# Initialize camera
cap = cv2.VideoCapture(0)  # Use 0 for default webcam

emotions = ['happy', 'sad', 'angry','neutral', 'surprise', 'fear', 'disgust']

# Dictionary to store emotion changes with timestamps
emotion_changes = dict({time.time():'neutral'}) # Start time : emotion -> Duration is start time [a] - start time [a+1]

global start_time
start_time = time.time()

last_time = time.time()

def get_emotion_duration(a,b,emotion_changes):
    """
    In an Intervall [a, b] get the amount of all emotions in that timeframe
    """
    # Get the keys (timestamps) from the dictionary
    timestamps = list(emotion_changes.keys())
    
    # Find the indices of the start and end timestamps
    start_index = max(0, next((i for i, t in enumerate(timestamps) if t >= a), len(timestamps) - 1))
    end_index = min(len(timestamps) - 1, next((i for i, t in enumerate(timestamps) if t >= b), len(timestamps) - 1))
    
    # Initialize a dictionary to store the duration of each emotion
    emotion_durations = {emotion: 0 for emotion in emotions}
    sliced_dict = {k: emotion_changes[k] for k in timestamps[start_index:end_index]}

    # Iterate through the sliced dictionary to calculate durations
    for i, (timestamp, emotion) in enumerate(sliced_dict.items()):
        if i < len(sliced_dict) - 1:
            next_timestamp = list(sliced_dict.keys())[i + 1]
        else:
            next_timestamp = b  # Use the end of the interval for the last entry

        # Add the duration for the current emotion
        emotion_durations[emotion] += next_timestamp - timestamp
        
    # Normalize the durations to get the percentage of time spent on each emotion
    total_duration = sum(emotion_durations.values())
    if total_duration > 0:
        for emotion in emotion_durations:
            emotion_durations[emotion] = (emotion_durations[emotion] / total_duration) * 100

    else:
        # If no duration is recorded, set all emotions to 0%
        for emotion in emotion_durations:
            emotion_durations[emotion] = 0.0
    
    return emotion_durations  

def get_emotion_last_xseconds(seconds, emotion_changes):
    if time.time() - seconds  < start_time:
        last_time = start_time
    else:
        last_time = time.time() - seconds
    # Get the biggest emotion in the last 5 seconds
    x_sec_distribution = get_emotion_duration(last_time, time.time(),emotion_changes)
    last_time = time.time()
    max_emotion = max(x_sec_distribution, key=x_sec_distribution.get)
    certainty = x_sec_distribution[max_emotion]
    if certainty < 30.0:
        return 'none', 0.0
    return max_emotion, certainty
    
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
        # Two Reaction "Types":
        # 1. Reaction to the Song -> Like or Dislike <- Kind of hard to measure 
        # Would mean to differentiate between song related and unrelated emotions and also being able to feed the information to a suitable algorithm
        # 2. Reaction unrelated to music -> Success / Focus / Neutral / Sadness / Anger 
        # This means that if in the last 10/5/3 seconds was a lot of anger, we can assume that the user is angry and we can react to that
        last_emotion = get_emotion_last_xseconds(5, emotion_changes)
        print(f"Last Emotion: {last_emotion[0]} with {last_emotion[1]}%")
        
        # Display results
        cv2.putText(frame, f"{last_emotion}", 
               (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 1)
    
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Show live feed
    cv2.imshow("Emotion Recognition", frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()