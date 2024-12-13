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
InputStream = None
OutputStream = None
Listening = False
FlagSwapping = False

def init(inp, out):
    global InputStream, OutputStream, FlagSwapping
    FlagSwapping = True
    _G.wait(0.5)
    try:
        InputStream = PAUDIO.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index = inp,
            frames_per_buffer=CHUNK
        )
    except Exception as err:
        _G.set_config('audio_input', 0)
        handle_exception(err)
        close_audio()
        _G.log_warning("Perhaps you selected wrong device, try others")
        FlagSwapping = False
        return
    try:
        OutputStream = PAUDIO.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            output=True,
            output_device_index=out,
            frames_per_buffer=CHUNK
        )
    except Exception as err:
        _G.set_config('audio_output', 0)
        handle_exception(err)
        close_audio()
        _G.log_warning("Perhaps you selected wrong device, try others")
        FlagSwapping = False
        return
    FlagSwapping = False
    _G.log_info("Audio ready")

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

def start_listening():
    global InputStream, OutputStream, Listening
    try:
        Listening = True
        while _G.FlagRunning:
            if FlagSwapping or not InputStream or not OutputStream:
                _G.uwait(_G.FPS)
                continue
            data = InputStream.read(CHUNK, exception_on_overflow=False)
            if _G.Config.get('playback'):
                audio_data = np.frombuffer(data, dtype=np.int16)
                audio_data = (audio_data * float(_G.Config.get('volume'))).astype(np.int16)
                data_out = audio_data.tobytes()
                OutputStream.write(data_out)
            if not _G.FlagWorking:
                continue
            samples = np.frombuffer(data, dtype=np.int16)
            fft_values = np.fft.rfft(samples)
            magnitudes = np.abs(fft_values)
            m_list = [int(n) for n in magnitudes[-5:]]
            DebugQueue.append(m_list)
            thresholds = _G.ARGV.get('threshold')
            if thresholds and all([v in  thresholds[i] for i,v in enumerate(m_list)]):
                _G.log_info("Passed thresholds:", m_list)
                _G.ARGV['fish_up'] = True
    except Exception as err:
        _G.log_error("Error while listening audio!")
        handle_exception(err)
        close_audio()
    finally:
        _G.log_info("Audio loop exited")
        Listening = False
        close_audio()

def list_devices():
    return [PAUDIO.get_device_info_by_index(i) for i in range(PAUDIO.get_device_count())]

def close_audio():
    global InputStream, OutputStream, FlagSwapping
    FlagSwapping = True
    _G.wait(0.5)
    _G.log_info("Audio closing")
    if InputStream:
        InputStream.stop_stream()
        InputStream.close()
    if OutputStream:
        OutputStream.stop_stream()
        OutputStream.close()
    InputStream = None
    OutputStream = None

def export_wave(filename):
    global DebugQueue
    with open(filename, 'a') as fp:
        fp.write('\n'.join([str([int(n) for n in ar]) for ar in DebugQueue]))
        fp.write('\n'+'-'*30+'\n')