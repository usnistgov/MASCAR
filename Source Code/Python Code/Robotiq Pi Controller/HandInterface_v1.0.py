#! ============================================================================================================
#! Original system:  MASCAR Testbed
#! Subsystem:        Robotiq gripper controller
#! Workfile:         HandInterface.py
#! Revision:         1.0 - 2 July, 2025
#! Author:           J. Marvel
#!
#! Description:      Script to control the Robotiq gripper using button interfaces on the GPIO.  Script also
#!                   creates a socket server to provide real-time feedback regading the gripper's state in JSON
#!                   format.
#! ============================================================================================================

#! General purpose imports
import time
import struct

#! For broadcasting gripper state
import socket
import sys

#! For gripper control
from gpiozero import Button
import pyRobotiqGripper

#! For multithreading the gripper control and the multicast server
import threading

MYPORT = 8123
MYGROUP_4 = '169.254.152.170'
MYGROUP_6 = 'ff15:7079:7468:6f6e:6465:6d6f:6d63:6173'
MYTTL = 1 # Increase to reach other networks

#! Global variables
gripper_ = pyRobotiqGripper.RobotiqGripper()
startTime_ = time.perf_counter()
stopTime_ = time.perf_counter()
strData_ = "Empty String"
sem_ = threading.Semaphore()
sem2_ = threading.Semaphore()
useJSON_ = True
buttonState_ = False
buttonEvent_ = time.perf_counter()
state_ = False

# @brief Gripper status update thread
#
def updateStatus():
    global strData_
    global gripper_
    global buttonState_
    global buttonEvent_
    global state_
    global sem_

    while True:
        sem2_.acquire()
        isActive = gripper_.isActivated()
        isCalib = gripper_.isCalibrated()
        pos_bits = gripper_.getPosition()
        if isCalib:
            pos_mm = gripper_.getPositionmm()
        else:
            pos_mm = -1.0
        button_state = buttonState_
        grip_state = state_
        button_time = buttonEvent_
        sem2_.release()
        
        sem_.acquire()
        if useJSON_:
            #Send data in JSON format
            strData_ = '''{{"GripperData": {{
  "act": "{}",
  "calib": "{}",
  "pbits": "{}",
  "pmm": "{}",
  "button": "{}",
  "grip": "{}",
  "actTime": "{}"}}
}}'''.format(isActive, isCalib, pos_bits, pos_mm, button_state, grip_state, button_time)
        else:
            #Default to XML
            strData_ = '''<?xml version="1.0" encoding="UTF-8"?>
<GripperData>
  <act>{}</act>
  <calib>{}</calib>
  <pbits>{}</pbits>
  <pmm>{}</pmm>
  <button>{}</button>
  <grip>{}</grip>
  <actTime>{}</actTime>
</GripperData>'''.format(isActive, isCalib, pos_bits, pos_mm, button_state, grip_state, button_time)
        #print(strData_)
        sem_.release()

        time.sleep(0.25)



# @brief Create and run a socket server
#
def sockSender():
    global strData_
    global sem_

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv_addr = ('', 10000)
    sock.bind(srv_addr)
    print("Starting up on ", sock.getsockname())
    sock.listen(1)

    while True:
        print ("Waiting for a connection")
        connection, client_address = sock.accept()
        try:
            print("Client connected: ", client_address)
            while True:
                sem_.acquire()
                #print(strData_)
                sndMe = strData_.encode("utf-8")
                sem_.release()
                connection.send(sndMe)

                # Update at 30Hz
                time.sleep(0.033)
        finally:
            connection.close()


# @brief Create and run a multicast server
#
def multiSender():
    # IPV4 or IPV6
    group = MYGROUP_4
    #group = MYGROUP_6

    addrinfo = socket.getaddrinfo(group, None)[0]

    # Create the socket
    s = socket.socket(addrinfo[0], socket.SOCK_DGRAM)

    # Set Time-to-live (optional)
    ttl_bin = struct.pack('@i', MYTTL)
    if addrinfo[0] == socket.AF_INET: # IPv4
        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
    else:
        s.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_MULTICAST_HOPS, ttl_bin)

    while True:
        data = repr(time.time()) + '\0'
        s.sendto(data.encode("utf-8"), (addrinfo[4][0], MYPORT))
        time.sleep(1)



# @brief Watch for momentary switch activity on GPIO 2.  
#
def button2Watcher():
    global gripper_
    global buttonState_
    global buttonEvent_
    global state_
    global sem2_

    button = Button(2)

    while True:
        button.wait_for_press()
        startTime_ = time.perf_counter()
        buttonState_ = True
        buttonTime_ = startTime_

        button.wait_for_release()
        stopTime_ = time.perf_counter()
        buttonState_ = False
        buttonTime_ = stopTime_

        elapseTime_ = stopTime_ - startTime_
        if elapseTime_ > 0.5:
            state_ = not state_
            sem2_.acquire()
            if state_:
                gripper_.open()
            else:
                gripper_.close()
            sem2_.release()


# @brief Watch for latching switch activity on GPIO 3
#
def button3Watcher():
    global gripper_
    global buttonState_
    global buttonEvent_
    global state_
    global sem2_

    button = Button(3)
    while True:
        newState = button.is_pressed
        if newState != state_:
            state_ = newState
            sem2_.acquire()
            if state_:
                gripper_.open()
            else:
                gripper_.close()
            sem2_.release()



# @brief Main program loop
#
def main():
    global gripper_
    global buttonState_
    global buttonEvent_
    global state_
    global sem2_

    # Spin off server thread
    t1 = threading.Thread(target=sockSender, name='SocketServer')
    t1.start()

    # Activate the gripper and have it go through its calibration routine    
    gripper_.activate()

    state_ = False
    time.sleep (1)
    gripper_.close()

    # Spin off gripper status thread
    t2 = threading.Thread(target=updateStatus, name='StatusUpdater')
    t2.start()

    # Spin off button 2 watcher - Wrist button
    #t3 = threading.Thread(target=button2Watcher, name='button2Watcher')
    #t3.start()

    # Spin off button 3 watcher - Remote button from relay
    # Spin off button 2 watcher - Wrist button
    t4 = threading.Thread(target=button3Watcher, name='button3Watcher')
    t4.start()

    button = Button(4)

    while True:
        button.wait_for_press()



if __name__ == "__main__":
    main()
