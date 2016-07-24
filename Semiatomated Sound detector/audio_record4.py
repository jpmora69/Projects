"""Audio capture and real-time root mean squared (RMS) calculation script
using a non-blocking implementation of PyAudio

- Don't forget to turn off active/auto noise cancellation on your recording device
- If you have an external microphone make use of that
- Please bring headphones to the lecture

Script will prompt for entry of the device number for audio input you'd like to use.
If entry is invalid, script will default to device '-1', which uses the system default device.

Usage:
>python audio_record.py

Requirements:
PyAudio: https://people.csail.mit.edu/hubert/pyaudio/

How to install:

Windows
>python -m pip install pyaudio

OSX
>brew install portaudio
>pip install pyaudio

Linux
>sudo apt-get install python-pyaudio python3-pyaudio

"""

__author__ = "Juan Mora - Based on the code of Charlie Mydlarz"
__version__ = "0.1"
__status__ = "Development"

import pyaudio
import time
import numpy as np
import wave
import datetime
import pandas as pd
import glob
import os
import sys

#Start the program and define a loop for a specific period of time
print ('Welcome to automated sound sensor V0.1')
print ('Starting program')
t_end = time.time() + (60 * 60 * 6)
while time.time() < t_end:
        
    # Declare variable global so other threads can make use of it
    global wavefile, recording, silence
    
    sample_rate = 44100                 # Sample rate of audio device
    frames_per_buffer = 2048            # Number of audio frames delivered per hardware buffer return
    channels = 1                        # Number of audio channels (1 = mono)
    fname = str(time.time()) + '.wav'   # Output wave filename using current UTC time
    csvname = str(time.time()) + '.csv' # Output csv filename using current UTC time
    total_duration = 1.0                # Total length of wave file
    device_id = -1                      # Default audio input device ID
    recording = True                    # Boolean check to hold while wait loop
    silence = 0                         # Boolean for determing wether to record or not  
    rmslist = []                        # List to store rms
    tslist = []                         # List to store Time stamps
    a = 0                               # dummy variable to temporary store rms
    b = 0                               # dummy variable to temporary store time stamps
    rmsdf = [[]]                        # Empty dataframe 1
    tsdf = [[]]                         # Empty dataframe 2
    
    # Initialize PyAudio
    pa = pyaudio.PyAudio() 
          
    def recorder_callback(in_data, frame_count, time_info, status_flags):
        """ This method is called whenever the audio device has acquired the number of audio samples
        defined in 'frames_per_buffer'. This method is called by a different thread to the main thread so some variables
        need to be declared global when altered within it. Avoid any heavy number crunching within this method as it
        can disrupt audio I/O if it blocks for too long.
        
        Args:
            in_data (str): Byte array of audio data from the audio input device.
            frame_count (int): Number of audio samples/frames received, will be equal to 'frames_per_nuffer'.
            time_info (dict): Dictionary of time information for audio sample data
            status_flags (long): Flag indicating any errors in audio capture
            """
    
        global wavefile, recording, silence    
          
        # Convert byte array data into numpy array with a range -1.0 to +1.0
        audio_data = np.fromstring(in_data, dtype=np.int16) / 32767.0
        
        # Calculate root mean squared of audio buffer
        rms = np.sqrt(np.mean(np.square(audio_data)))# Print RMS to console       
        
        #Defining threadshold for triggering recording and rms logging        
        if rms > 0.05:    
            a = rms
            b = ('{:%Y-%m-%d %H:%M:%S:%f}'.format(datetime.datetime.now()))
            tslist.append(b)
            rmslist.append(a)        
            print rms
            print ('{:%Y-%m-%d %H:%M:%S:%f}'.format(datetime.datetime.now())) 
            rmsdf = pd.DataFrame(rmslist, columns=['rms'])
            tsdf = pd.DataFrame(tslist, columns=['Date-time'])
            rmsts = pd.concat([rmsdf, tsdf], axis=1)
            rmsts.to_csv(csvname)  
            silence = 1
        
        #Triggering recording based on the threadshold          
        if silence == 1:    
            # Write audio byte array values to wave file
            wavefile.writeframes(in_data) 
            
            # If wavefile length is equal to the duration and less than the 
            # RMS threasdhold given then change recording flag
            if wavefile.getnframes() > total_duration * sample_rate and rms < 0.02:
                recording = False
         
        return None, pyaudio.paContinue
                     
    #Initialize recording stream object passing all predefined settings
    
    recorder = pa.open(start=False,
                   format=pyaudio.paInt16,
                   channels=channels,
                   rate=sample_rate,
                   input=True,
                   frames_per_buffer=frames_per_buffer,
                   stream_callback=recorder_callback)
    
    
    # Open wave file ready for I/O
    wavefile = wave.open(fname, 'wb')   
    # Set number of input channels
    wavefile.setnchannels(channels)
    # Set sample width = 2, as each 16bit sample value consists of 2 bytes: http://wavefilegem.com/how_wave_files_work.html
    wavefile.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
    # Set sample rate at 44,100 sample values per second
    wavefile.setframerate(sample_rate)   
    
    # Start recording stream, triggering hardware buffer fill and callback
    recorder.start_stream()        
       
    # Hold script in loop waiting for wave file to meet desired file length in seconds
    while recording:
        time.sleep(0.1)
    # Close all open streams and files
    #recorder.stop_stream()
    recorder.close()
    wavefile.close()   
    pa.terminate()        

"""After the loop for recording is finished, concatenate all csv created with the
RMS values and timestamps and create a plot
The script auto detects the path in which the script is placed and uses it as the
defined path for reading the csv files""" 

path = os.path.abspath(os.path.dirname(sys.argv[0]))
allFiles = glob.glob(path + "/*.csv")
frame = pd.DataFrame()
list_ = []
for file_ in allFiles:
    df = pd.read_csv(file_,index_col=None, header=0)
    list_.append(df)
frame = pd.concat(list_)
frame = frame.reset_index()
frame = frame.drop(frame.columns[[0, 1]], axis=1)
frame = frame.set_index(['Date-time'])
ax = frame.plot(figsize=(18,8), rot=45, grid=True)
ax.set_xlabel("Date and time", fontsize = 10)
ax.set_ylabel("RMS", fontsize = 12)
ax.set_title('RMS variation', fontsize = 16)

#Say goodbye and terminate the program
print ('Terminating program, Goodbye!')