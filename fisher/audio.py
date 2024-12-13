import _G
import numpy as np
import pyaudio
import wave
from utils import handle_exception
from collections import deque

sound = True
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
DEBUG_REWIND_SECONDS = 5
PAUDIO = pyaudio.PyAudio()

def play_file(file, output_index):
    try:
        wf = wave.open(file, 'rb')
        stream = PAUDIO.open(
            format=PAUDIO.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=output_index
        )
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream()
        stream.close()
        wf.close()
        _G.log_info(f"Finished playing: {file}")
    
    except FileNotFoundError:
        _G.log_error(f"File not found: {file}")
    except Exception as e:
        _G.log_error(f"An error occurred while playing the file: {e}")
        handle_exception(e)
        

DebugQueue = deque(maxlen=int(RATE / CHUNK * DEBUG_REWIND_SECONDS))

def listen_fishing(thresholds, input_device, output_device, playback=True):
    _G.log_info(f"Fishing start, parameters:\nth={thresholds}\nid={input_device}\nod={output_device}\npb={playback}")
    input_stream = PAUDIO.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        input_device_index = input_device,
        frames_per_buffer=CHUNK
    )
    if playback:
        output_stream = PAUDIO.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            output_device_index=output_device,
            frames_per_buffer=CHUNK
        )
    try:
        while True:
            data = input_stream.read(CHUNK, exception_on_overflow=False)
            if playback:
                output_stream.write(data)
            samples = np.frombuffer(data, dtype=np.int16)
            fft_values = np.fft.rfft(samples)
            magnitudes = np.abs(fft_values)
            m_list = [int(n) for n in magnitudes[-5:]]
            DebugQueue.append(m_list)
            if all([v in thresholds[i] for i,v in enumerate(m_list)]):
                _G.log_info("Passed thresholds:", m_list)
                break
    finally:
        input_stream.stop_stream()
        input_stream.close()
        output_stream.stop_stream()
        output_stream.close()
    return True

def list_devices():
    return [PAUDIO.get_device_info_by_index(i) for i in range(PAUDIO.get_device_count())]