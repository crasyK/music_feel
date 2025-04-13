import time
emotions = ['happy', 'sad', 'angry','neutral', 'surprise', 'fear', 'disgust']

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

def get_emotion_last_xseconds(seconds, emotion_changes, start_time):
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