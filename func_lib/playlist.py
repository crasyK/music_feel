import sclib
import requests
import sounddevice as sd
import io
import soundfile as sf
import threading
import time
import numpy as np # Import numpy for silence generation

# Define buffer size for audio chunks
BLOCK_SIZE = 1024 * 4 # Adjust as needed for performance/latency balance

class SoundCloudPlayer:
    def __init__(self):
        self.api = sclib.SoundcloudAPI()
        self.playlist = None
        self.current_track_index = 0
        self.is_playing = False      
        self.is_paused = False       
        self.is_interrupted = False  
        self.stop_requested = False  
        self.interrupt_track_url = None

        self.lock = threading.Lock() 
        self.pause_event = threading.Event() 
        self.stream_finished_event = threading.Event() 


        self.stream = None           
        self.current_sf = None       
        self.current_response = None 
        self.stream_thread = None    

        self.pause_event.set() 

    def _audio_callback(self, outdata, frames, time_info, status):
        if status:
            print("Stream status:", status, flush=True)


        with self.lock:

            if self.stop_requested or self.is_interrupted:
                outdata[:] = 0 
                self.stream_finished_event.set()
                raise sd.CallbackStop("Playback stopped or interrupted.")

            if self.is_paused:

                self.lock.release()
                self.pause_event.wait() 
                self.lock.acquire() 
                if self.stop_requested or self.is_interrupted:
                    outdata[:] = 0
                    self.stream_finished_event.set()
                    raise sd.CallbackStop("Playback stopped or interrupted post-pause.")

            try:
                read_data = self.current_sf.read(frames=frames, dtype='float32', always_2d=True)

                if read_data.shape[0] == 0: 
                    outdata[:] = 0 
                    self.stream_finished_event.set() 
                    raise sd.CallbackStop("End of track reached.")

                outdata[:read_data.shape[0]] = read_data

                if read_data.shape[0] < frames:
                    outdata[read_data.shape[0]:] = 0
                    self.stream_finished_event.set() 
                    raise sd.CallbackStop("End of track reached with padding.")

            except Exception as e:
                print(f"Error during audio callback: {e}", flush=True)
                outdata[:] = 0 
                self.stream_finished_event.set()
                raise sd.CallbackStop("Error reading audio data.")

    def _close_stream_resources(self):
        if self.stream:
            try:
                if not self.stream.closed:
                    self.stream.stop()
                    self.stream.close()
            except Exception as e:
                print(f"Error closing stream: {e}", flush=True)
            self.stream = None
        if self.current_sf:
            try:
                self.current_sf.close()
            except Exception as e:
                print(f"Error closing soundfile: {e}", flush=True)
            self.current_sf = None
        if self.current_response:
            try:
                self.current_response.close() 
            except Exception as e:
                print(f"Error closing response: {e}", flush=True)
            self.current_response = None


    def _play_track_streaming(self, track):
        try:
            stream_url = track.get_stream_url()
            if not stream_url:
                print(f"Stream URL not found for {track.title}.", flush=True)
                return False # Indicate failure

            print(f"Streaming: {track.title}", flush=True)
            self.current_response = requests.get(stream_url, stream=True)
            self.current_response.raise_for_status()
            
            file_like_object = io.BytesIO(self.current_response.content)
            file_like_object.seek(0)

            self.current_sf = sf.SoundFile(file_like_object)

            self.stream_finished_event.clear()
            
            self.stream = sd.OutputStream(
                samplerate=self.current_sf.samplerate,
                channels=self.current_sf.channels,
                blocksize=BLOCK_SIZE, 
                callback=self._audio_callback,
                finished_callback=self.stream_finished_event.set 
            )
            self.stream.start()
            return True 

        except requests.exceptions.RequestException as e:
            print(f"Network error fetching track {track.title}: {e}", flush=True)
        except sf.SoundFileError as e:
             print(f"Error opening soundfile for {track.title}: {e}", flush=True)
        except sd.PortAudioError as e:
             print(f"Sound device error for {track.title}: {e}", flush=True)
        except Exception as e:
            print(f"Error preparing track {track.title}: {e}", flush=True)

        self._close_stream_resources() 
        self.stream_finished_event.set()
        return False 

    def _play_playlist_loop(self):
        """The main loop running in a separate thread."""
        while True:
            current_track_object = None
            play_this_track = False

            with self.lock:
                if self.stop_requested:
                    self.is_playing = False
                    break 

                if self.is_interrupted:
                    url_to_play = self.interrupt_track_url
                    self.interrupt_track_url = None 
                    self.is_interrupted = False 

                    try:
                        current_track_object = self.api.resolve(url_to_play)
                        play_this_track = True
                        print(f"--- Interrupting with: {current_track_object.title} ---", flush=True)
                    except Exception as e:
                        print(f"Error resolving interrupt track {url_to_play}: {e}", flush=True)
                        continue # Skip to next iteration

                elif self.playlist is None or self.current_track_index >= len(self.playlist.tracks):
                    self.is_playing = False
                    break 


                else:
                    current_track_object = self.playlist.tracks[self.current_track_index]
                    play_this_track = True
                    print(f"\nNow playing: {current_track_object.title} ({self.current_track_index + 1}/{len(self.playlist.tracks)})", flush=True)

            if play_this_track and current_track_object:
                started_ok = self._play_track_streaming(current_track_object)

                if started_ok:
                    self.stream_finished_event.wait()
                    
                    with self.lock:
                        self._close_stream_resources()
                        
                        if not self.is_interrupted and not self.stop_requested and current_track_object == self.playlist.tracks[self.current_track_index]:
                             self.current_track_index += 1
                else:
                    
                    print(f"Skipping track {current_track_object.title} due to error.", flush=True)
                    with self.lock:
                         if current_track_object == self.playlist.tracks[self.current_track_index]:
                            self.current_track_index += 1 

            time.sleep(0.1)


        with self.lock:
            self.is_playing = False
            self._close_stream_resources()


    def start_playlist(self, playlist_url):
        with self.lock:
            if self.is_playing:
                print("Player is already playing. Stop first.", flush=True)
                return

            try:
                print("Resolving playlist...", flush=True)
                self.playlist = self.api.resolve(playlist_url)
                if not isinstance(self.playlist, sclib.Playlist):
                     print(f"Resolved URL is not a playlist ({type(self.playlist)}).", flush=True)
                     self.playlist = None
                     return
                if not self.playlist.tracks:
                    print("Playlist is empty.", flush=True)
                    self.playlist = None
                    return
                print(f"Playlist '{self.playlist.title}' loaded with {len(self.playlist.tracks)} tracks.", flush=True)
            except Exception as e:
                print(f"Error resolving playlist {playlist_url}: {e}", flush=True)
                self.playlist = None
                return

            self.current_track_index = 0
            self.is_playing = True
            self.stop_requested = False
            self.is_interrupted = False
            self.is_paused = False
            self.pause_event.set() 
            
            self.stream_thread = threading.Thread(target=self._play_playlist_loop, daemon=True)
            self.stream_thread.start()

    def interrupt(self, track_url):
        with self.lock:
            if not self.is_playing:
                print("Cannot interrupt: Player is not playing.", flush=True)
                return

            print("Interrupt requested.", flush=True)
            self.is_interrupted = True
            self.interrupt_track_url = track_url
            if self.stream and not self.stream.stopped:
                 pass 

    def stop(self):
        with self.lock:
            if not self.is_playing and not self.is_paused:
                 return
            print("Stop requested.", flush=True)
            self.stop_requested = True 
            self.is_playing = False 
            self.is_paused = False 
            self.pause_event.set()
            self.stream_finished_event.set()

        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=1.0)


    def pause(self):
        with self.lock:
            if not self.is_playing or self.is_paused:
                print("Cannot pause: Player not playing or already paused.", flush=True)
                return
            print("Pausing...", flush=True)
            self.is_paused = True
            self.pause_event.clear()


    def resume(self):
        """Resumes playback."""
        with self.lock:
            if not self.is_playing or not self.is_paused:
                print("Cannot resume: Player not playing or not paused.", flush=True)
                return
            print("Resuming...", flush=True)
            self.is_paused = False
            self.pause_event.set()
