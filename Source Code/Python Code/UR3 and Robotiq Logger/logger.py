#! ============================================================================================================
#! Original system:  MASCAR Testbed
#! Subsystem:        Robot data logger
#! Workfile:         logger.py
#! Revision:         1.0 - 2 July, 2025
#! Author:           J. Marvel
#!
#! Description:      Script to record data from a universal robot via the RTDE and the attached Robotiq gripper
#!                   via socket connections.  Script collects data and stores it to individual data files with
#!                   the date and time as identifiers regarding when they were collected. 
#! 
#! Notes:            To do:  Store everything in ROSBag2 files
#! ============================================================================================================

# For multithreading the different recorder functions
import threading
import datetime

import pyaudio
import wave

import logging
import socket
import sys

import time

import keyboard

sys.path.append("..")
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import rtde.csv_writer as csv_writer
import rtde.csv_binary_writer as csv_binary_writer

#! Global variables used by the different threads
running_ = True
recording_ = False
timestr_ = datetime.datetime.now().strftime("%Y%B%d_%I%M")
index_ = -1

gripperRec_ = False
UR3Rec_ = False
timeRec_ = False



# @brief Launch and run in a new thread the gripper status recorder
#
# =============================================================================================================
def gripper_recorder():
    global running_
    global recording_
    global timestr_
    global gripperRec_

    HOST = "169.254.116.100"    #! The server's hostname or IP address
    PORT = 10000                #! The port used by the server
    writeModes = "w"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        while running_:
            if recording_:
                gripperRec_ = True
                gripperfilename = timestr_ + "_gripper.json"
                with open(gripperfilename, writeModes) as gripperfile:
                    print ("Recording gripper state data")
                    #! Loop until instructed to stop by the main program
                    while recording_:
                        data = s.recv(4096)
                        prntMe = data.decode("utf-8")
                        gripperfile.writelines(prntMe)
                # with open(gripperfilename, writeModes) as gripperfile:
                #! with open() automatically closes the file when completed
                print("Finished writing gripper log file")
            gripperRec_ = False
        # while running_
# =============================================================================================================




# @brief Launch and run in a new thread the audio recorder
#
# =============================================================================================================
def timecode_recorder():
    form_1 = pyaudio.paInt16   #! 16-bit resolution
    chans = 1                  #! 1 channel
    samp_rate = 44100          #! 44.1 kHz sampling
    chunk = 4096               #! 4k samples for buffer

    global running_
    global recording_
    global timestr_
    global index_
    global timeRec_

    #! Create the Python audio instantiation
    audio = pyaudio.PyAudio()
    print ("Opening audio on device index " + str(index_))

    stream = audio.open(format = form_1, rate = samp_rate, channels = chans,\
                        input_device_index = index_, input = True, \
                        frames_per_buffer = chunk)
    stream.stop_stream()
    stream.close()

    #! Loop until told by the main program function to quit
    while running_:

        if recording_:
            timeRec_ = True
            print ("Recording time code data")
            stream = audio.open(format = form_1, rate = samp_rate, channels = chans,\
                                input_device_index = index_, input = True, \
                                frames_per_buffer = chunk)
            wavfilename = timestr_ + "_audio.wav"

            frames = []

            #! Loop until told by the main program function to stop recordng
            while recording_:
                data = stream.read(chunk)
                frames.append(data)

            print ("Finalizing time code data log")
            stream.stop_stream()
            stream.close()

            wavfile = wave.open(wavfilename, 'wb')
            wavfile.setnchannels(chans)
            wavfile.setsampwidth(audio.get_sample_size(form_1))
            wavfile.setframerate(samp_rate)
            wavfile.writeframes(b''.join(frames))
            wavfile.close()
            print("Finished writing timecode file")
            timeRec_ = False

    print("Timecode recorder quitting...")
    audio.terminate()
# =============================================================================================================
          

# @brief Launch and run in a new thread the UR RTDE recorder
#
# =============================================================================================================
def rtde_recorder():
    global running_
    global recording_
    global timestr_
    global UR3Rec_

    verbose = True
    host = "169.254.152.41"   #! TODO:  Replace with IP address of UR controller
    port = 30004
    freq = 125
    binary = False

    if verbose:
        logging.basicConfig(level=logging.INFO)
    conf = rtde_config.ConfigFile("logger.xml")
    output_names, output_types = conf.get_recipe("out")

    #! Connect to the robot controller
    con = rtde.RTDE(host, port)
    con.connect()
    #! Get controller version
    con.get_controller_version()
    #! Set up recipes
    if not con.send_output_setup(output_names, output_types, frequency=freq):
        logging.error("Unable to configure output")
        sys.exit()
    #! Start data synchronization
    if not con.send_start():
        logging.error("Unable to start synchronization")
        sys.exit()
    writeModes = "wb" if binary else "w"

    while running_:

        if recording_:
            rtdefilename = timestr_ + "_rtde.csv"
            rtdetimefile = timestr_ + "_rtde_timestamps.csv"

            #                with open(gripperfilename, writeModes) as gripperfile:
            #                    print ("Recording gripper state data")
            #                    #! Loop until instructed to stop by the main program
            #                    while recording_:
            #                        data = s.recv(4096)
            #                        prntMe = data.decode("utf-8")
            #                        gripperfile.write(prntMe)

            with open(rtdefilename, writeModes) as csvfile:
                writer = None
                UR3Rec_ = True
                if binary:
                    writer = csv_binary_writer.CSVBinaryWriter(csvfile, output_names, output_types)
                else:
                    writer = csv_writer.CSVWriter(csvfile, output_names, output_types)

                print ("Recording UR3 state data")
                writer.writeheader()

                #! Loop until instructed to stop by the main program
                while recording_:
                    try:
                        #state = con.receive_buffered(binary)
                        state = con.receive(binary)               #! Only get the most recent message
                        if state is not None:
                            timstr = datetime.datetime.now()
                            writer.writerow(state)

                    except rtde.RTDEException:
                        con.disconnect()
                        sys.exit()
                UR3Rec_ = False
            print("Finished writing UR3 log file")
            # with open(rtdefilename, writeModes) as csvfile
            #! with open() automatically closes the file when completed

            print ("Finalizing UR3 timestamp log")
    # while running_

    #! Close the connection to the robot controller
    con.send_pause()
    con.disconnect()
# =============================================================================================================


# @brief Main program function
#
# =============================================================================================================
def main():
    global timestr_
    global recording_
    global running_
    global index_

    global gripperRec_
    global timeRec_
    global UR3Rec_

    p = pyaudio.PyAudio()
    for ii in range(p.get_device_count()):
        print(f"{ii} {p.get_device_info_by_index(ii).get('name')}")

    inval = input("Select audio input to record:  ")
    index_ = int(inval)

    running_ = True
    state = False
    
    #t1 = threading.Thread(target=timecode_recorder, name='TimecodeRecorder')
    #t1.start()

    #t2 = threading.Thread(target=rtde_recorder, name='RTDERecorder')
    #t2.start()

    t3 = threading.Thread(target=gripper_recorder, name='GripperRecorder')
    t3.start()

    print("Type rec to start/stop recording, quit to exit the program\n")

    while running_:
        inval = input("input:  ")

        if inval == "rec":
            timestr_ = datetime.datetime.now().strftime("%Y%B%d_%I%M")
            recording_ = not recording_
            if recording_:
                print ("Recording started")
            else:
                print ("Recording stopped.  Waiting for log files to complete.")
                state = not gripperRec_ and not timeRec_ and not UR3Rec_
                while not state:
                   time.sleep(1)
                   state = not gripperRec_ and not timeRec_ and not UR3Rec_
                # To do:  combine all files into ROSBag
        elif inval == "quit":
            print ("Quitting...")
            recording_ = False
            running_ = False
# =============================================================================================================


if __name__ == "__main__":
    main()