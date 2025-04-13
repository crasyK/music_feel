import sclib
import requests
import sounddevice as sd
import io
import soundfile as sf
import threading
import time

class SoundCloudPlayer:
    def __init__(self):
        self.api = sclib.SoundcloudAPI()
        self.playlist = None
        self.current_track_index = 0
        self.is_playing = False
        self.is_paused = False  
        self.is_interrupted = False
        self.interrupt_track_url = None
        self.lock = threading.Lock()
        self.pause_event = threading.Event() 

    def play_track(self, track):
        try:
            stream_url = track.get_stream_url()
            if not stream_url:
                print(f"Stream URL not found for {track.title}.")
                return

            response = requests.get(stream_url, stream=True)
            response.raise_for_status()

            with io.BytesIO() as buffer:
                for chunk in response.iter_content(chunk_size=4096):
                    if chunk:
                        buffer.write(chunk)
                        with self.lock:
                            if self.is_interrupted:
                                break #interrupt the song.
                buffer.seek(0)
                data, samplerate = sf.read(buffer)
                if not self.is_interrupted:
                    sd.play(data, samplerate)
                    sd.wait()

        except Exception as e:
            print(f"Error playing track: {e}")

    def play_playlist(self):
        with self.lock:
            self.is_playing = True
        while self.is_playing and self.current_track_index < len(self.playlist.tracks):
            if self.is_interrupted:
                with self.lock:
                    self.is_interrupted = False
                self.play_track(self.api.resolve(self.interrupt_track_url))
            if not self.is_playing:
                break;
            track = self.playlist.tracks[self.current_track_index]
            print(f"Now playing: {track.title}")
            self.play_track(track)
            self.current_track_index += 1
            time.sleep(1) #slight pause between songs.
        with self.lock:
            self.is_playing = False

    def start_playlist(self, playlist_url):
        self.playlist = self.api.resolve(playlist_url)
        self.current_track_index = 0
        threading.Thread(target=self.play_playlist).start()

    def interrupt(self, track_url):
        with self.lock:
            if self.is_playing:
                self.is_interrupted = True
                self.interrupt_track_url = track_url
        sd.stop() #stop the current song.

    def stop(self):
        with self.lock:
            self.is_playing = False
        sd.stop() #replace with your interrupt song.
        
    def pause(self):
        with self.lock:
            self.is_paused = True
        sd.stop() #stop playing the current sound.
        time.sleep(3) #wait for the sound to stop.
