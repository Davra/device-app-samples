# A Sample Device Application
# This imports the Davra Device SDK
# Which connects to the Davra Device Agent
# and from there to the Davra server
#
import time, requests, os.path
from requests.auth import HTTPBasicAuth
import json, sys
from pprint import pprint
from datetime import datetime
import davra_sdk as davraSdk
# Required to access raspberry pi hardware
import RPi.GPIO as GPIO


# Configuration for the app should be available in config.txt.
# It should contain the application name and version
appConfig = davraSdk.loadAppConfiguration()



###########################   FUNCTIONS THIS APP CAN PERFORM

# Initial GPIO setup
GPIO.setmode(GPIO.BOARD)
GPIO.setup(12, GPIO.OUT)
p = GPIO.PWM(12, 50)
p.start(0)

# Turn Motor Left
def motorLeft(functionInfo):
    davraSdk.log('App received instruction to Turn Left ' + str(functionInfo))
    p.ChangeDutyCycle(3)  # turn towards 0 degree
    # Set the function (job) as complete
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": "Motor moved" })
    # Demonstration of sending alarm event from app to server via agent
    davraSdk.sendIotData({"name": "davranetworks.alarm", "msg_type": "event", \
    "value": {"message": "sampleAppMotor Left", "severity": "INFO", "config": { "name": "sampleAppMotor Left"}}})



# Turn motor Right
def motorRight(functionInfo):
    davraSdk.log('App received instruction to Turn Off Led ' + str(functionInfo))
    p.ChangeDutyCycle(7)  # turn towards 0 degree
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": "Motor moved" })
    # Demonstration of sending alarm event from app to server via agent
    davraSdk.sendIotData({"name": "davranetworks.alarm", "msg_type": "event", \
    "value": {"message": "sampleAppMotor Right", "severity": "INFO", "config": { "name": "sampleAppMotor Right"}}})


###########################   MAIN LOOP

if __name__ == "__main__":
    
    davraSdk.log("Starting device application " + appConfig["applicationName"] + " " + appConfig["applicationVersion"])
    
    # Instruct the SDK to attach to the mqtt topic and call our function when a message is received
    # Also inform the SDK of the name of this Device Application
    davraSdk.connectToAgent(appConfig["applicationName"])
    # Wait (for a max of timeout seconds) until the agent is available to communicate
    davraSdk.waitUntilAgentIsConnected(600)
    
    # Inform the Agent and Platform server that this application can do tasks on the device
    davraSdk.registerCapability('agent-action-motorLeft', { \
            "functionParameters": { }, \
            "functionLabel": "Turn Motor Left", \
            "functionDescription": "Turn the motor left" \
    }, motorLeft)
    davraSdk.registerCapability('agent-action-motorRight', { \
            "functionParameters": { }, \
            "functionLabel": "Turn Motor Right", \
            "functionDescription": "Turn the motor right" \
    }, motorRight)
    
    # Demonstrate at startup the motor is funnctioning
    p.ChangeDutyCycle(0)
    time.sleep(1)
    p.ChangeDutyCycle(7) 
    time.sleep(1)
    p.ChangeDutyCycle(3) 
    countMainLoop = 0

    # Main loop to run forever. 
    while True:
        # Only every n seconds
        if(countMainLoop % 60 == 0):
            davraSdk.log('Application running: ' + appConfig["applicationName"])
        # Loop once per second
        countMainLoop += 1
        time.sleep(1)
# End Main loop