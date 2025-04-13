# MusicFeel DJ 😎 - Your Emotion-Reactive Music Buddy!

Ever wish your music just *knew* how you were feeling? Like, you're super hyped after finally fixing that bug, and you need a triumphant fanfare? Or maybe you're feeling the coding rage and need some chill lofi to calm down?

Well, buckle up, because this little Python script tries to do just that! It watches your face, figures out your vibe, and throws on the perfect (or at least, a *situationally appropriate*) track from SoundCloud to match your mood.

## What's the Vibe? ✨

This script uses your webcam to:

1.  **See Your Face:** Uses OpenCV to grab video frames.
2.  **Read Your Mood:** Leverages the magic of `deepface` to detect your dominant emotion (happy, sad, angry, fear, neutral, etc.) in real-time.
3.  **Spin Some Tunes:** Plays a SoundCloud playlist you provide using a custom player #
4.  **React & Interrupt:** If it detects a strong emotion (like you've been happy, sad, or angry for a bit):
    * It **pauses** the current playlist track.
    * Uses Text-to-Speech to **announce** the mood change (because why not?).
    * **Interrupts** with a special SoundCloud track fitting that emotion (like trumpets for joy, or lofi for anger).
    * Once the special track is done, it *should* go back to your playlist (the player handles this!).
5.  **Keep Grooving:** Continues monitoring your mood and the music.

Think of it as your personal AI DJ that *tries* to get you. Sometimes it might be spot on, sometimes hilariously wrong, but hey, that's part of the fun!
## Getting Started 🚀

Ready to sync your mood with music?

**Prerequisites:**

* Python 3.x installed (Check with `python --version`).
* A webcam connected to your computer (Gotta see that lovely face!).
* An internet connection (For SoundCloud streaming and downloading the DeepFace magic models).

**Installation:**

1.  **Clone the Fun:** Grab the code from wherever it lives (e.g., GitHub).
    ```bash
    git clone https://github.com/crasyK/music_feel.git
    cd music_feel
    ```

2.  **Set Up Shop (Virtual Environment Recommended!):**
    Keep things tidy!
    ```bash
    # Create a virtual environment named 'venv'
    python -m venv venv

    # Activate it:
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install the Magic Spells (Dependencies):**
    Now, let's get the libraries needed.
    ```bash
    pip install -r requirements.txt
    ```

**Usage:**

1.  **Run the Script:**
    Make sure your virtual environment is active!
    ```bash
    python main.py
    ```

2.  **Enter Playlist:** The script will ask for a SoundCloud playlist URL in your terminal. Paste one in (like `https://soundcloud.com/discover/sets/techno` or your favorite techno/lofi/whatever list) and hit Enter.
    *(Remember: Use a playlist URL, not just a single track or user profile!)*

3.  **Face the Music:** Look towards your webcam! A window should pop up showing the video feed, probably with your detected emotion written on it.

4.  **React!:** Try making different faces! Smile big, look dramatically sad, pretend to be coding-angry (we've all been there). See if you can trigger the special mood tracks.

5.  **All Done?** Press the 'q' key while the webcam window is selected (in focus) to stop the script and close everything down nicely.

## Make it Your Own 🔧💡

Want to personalize your AI DJ? Dive into the main script (`main.py`) and tweak away:

* **Change the Mood Music:** Don't like the trumpet fanfare for happiness? Find the lines like `player.interrupt("https://soundcloud.com/...")` for each emotion (`happy`, `sad`, `angry`, `fear`) and paste in different SoundCloud track URLs. Go wild!
* **Adjust Emotion Sensitivity:** Feeling like it triggers too easily or not enough? Modify the percentage thresholds (`> 40.0`, `> 80.0`) in the `if last_emotion[0] == '...'` conditions.
* **Modify Checking Frequency:** Change the `counter_every = 3` variable (how many seconds between major emotion checks) or the duration used in `get_emotion_last_xseconds(5, ...)` (how many past seconds to consider for the dominant mood check).
* **Customize Robot Voice:** Edit the `engine.say("...")` lines to make the Text-to-Speech announcements say whatever funny or cool things you want!

## Disclaimer Corner 🤔

* **Emotion detection isn't mind-reading!** Things like bad lighting, weird camera angles, hats, glasses, or just the inherent limits of the AI models can affect accuracy. Sometimes 'neutral' looks like 'sad', it happens!
* **This is for fun!** It's a cool tech demo, not a replacement for actual therapy or understanding complex human feelings.
* **Needs Internet:** Streaming music and sometimes downloading AI models requires a stable connection.
* **CPU Heavy:** Real-time video analysis can make your computer's fan spin up. Performance varies depending on your hardware.

---

Hope you have a blast with your personalized MusicFeel DJ! Let the good (or appropriately themed) times roll! 🎧😌