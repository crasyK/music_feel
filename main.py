import cv2
from deepface import DeepFace
import time

# Initialize camera
cap = cv2.VideoCapture(0)  # Use 0 for default webcam

emotions = ['happy', 'sad', 'angry','neutral', 'surprise', 'fear', 'disgust']

# Dictionary to store emotion changes with timestamps
emotion_changes = dict({time.time():'neutral'}) # Start time : emotion -> Duration is start time [a] - start time [a+1]

start_time = time.time()

def get_emotion_duration(a,b,emotion_changes):
    """
    In an Intervall [a, b] get the amount of all emotions in that timeframe
    """
    # Get the keys (timestamps) from the dictionary
    timestamps = list(emotion_changes.keys())
    
    # Find the indices of the start and end timestamps
    start_index = max(0, next((i for i, t in enumerate(timestamps) if t >= a), len(timestamps) - 1))
    end_index = min(len(timestamps) - 1, next((i for i, t in enumerate(timestamps) if t >= b), len(timestamps) - 1))
    
    sliced_dict = {k: emotion_changes[k] for k in timestamps[start_index:end_index]}
    return sliced_dict   
    
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
            
        
        emotion_distribution =  get_emotion_duration(start_time, time.time(),emotion_changes)
        
        # Print the emotion distribution
        print("Emotion Distribution:") 
        print(emotion_distribution)
        # Display results
        cv2.putText(frame, f"{dominant_emotion} ({confidence:.1f}%)", 
                   (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
        
    except Exception as e:
        print(f"Error: {e}")
    
    # Show live feed
    cv2.imshow("Emotion Recognition", frame)
    
    # Exit on 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()