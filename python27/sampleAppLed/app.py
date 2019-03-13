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
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.OUT, initial=GPIO.LOW)

# Turn On the LED
def ledTurnOn(functionInfo):
    global ledDutyCycle
    davraSdk.log('App received instruction to Turn On Led ' + str(functionInfo))
    GPIO.output(27, GPIO.HIGH)
    ledDutyCycle = -1
    # Set the function (job) as complete
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": "Led was turned on" })
    # Demonstration of sending event from app to server via agent
    davraSdk.sendIotData({"name": "sampleAppLed.ledOn", "msg_type": "event", \
    "value": {"message": "Led turned on", "severity": "INFO"}})


# Turn off the LED
def ledTurnOff(functionInfo):
    global ledDutyCycle
    davraSdk.log('App received instruction to Turn Off Led ' + str(functionInfo))
    GPIO.output(27, GPIO.LOW)
    ledDutyCycle = -1
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": "Led was turned off" })


# Flash the Led on and off at the supplied frequency. Eg 1=Once per second
ledDutyCycle = -1 # Seconds for cycling the led flashing. -1 indicates not in use.
def ledFlash(functionInfo):
    global ledDutyCycle
    davraSdk.log('App received instruction to set Led flash ')
    if("functionParameterValues" in functionInfo and "LED Duty cycle (secs)" in functionInfo["functionParameterValues"] \
    and int(functionInfo["functionParameterValues"]["LED Duty cycle (secs)"]) > 0):
        davraSdk.log('App to set ledFlash ' + str(functionInfo["functionParameterValues"]["LED Duty cycle (secs)"]))
        ledDutyCycle = int(functionInfo["functionParameterValues"]["LED Duty cycle (secs)"])
        davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
        "status": "completed", \
        "response": "Led was set with a duty cycle of " + str(ledDutyCycle) })
    else:
        davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
        "status": "failed", \
        "response": "Led was not set because the duty cycle was missing" })


# Get a process listing from this device
def getProcessListing(functionInfo):
    davraSdk.log('App received instruction to get process listing ')
    s = davraSdk.runCommandWithTimeout("ps -ef ", 10)
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": str(s[1]) })
    return


# Just for demonstration purposes
# A callback for when any message is seen on the comms channel from the agent.
def onAnyMessageReceived(msg):
    payload = str(msg.payload)
    if(davraSdk.isJson(payload) == False):
        return
    msg = json.loads(payload)
    # Was this message from this app itself
    if("fromApp" in msg and msg['fromApp'] == appConfig["applicationName"]):
        return
    else:
        # Was this message from the Device Agent
        if("fromAgent" in msg):
            davraSdk.log("A message was received from Device Agent")
    return

    
    
###########################   MAIN LOOP

if __name__ == "__main__":
    
    davraSdk.log("Starting device application " + appConfig["applicationName"] + " " + appConfig["applicationVersion"])
    
    # Instruct the SDK to attach to the mqtt topic and call our function when a message is received
    # Also inform the SDK of the name of this Device Application
    davraSdk.connectToAgent(appConfig["applicationName"])
    # Wait (for a max of timeout seconds) until the agent is available to communicate
    davraSdk.waitUntilAgentIsConnected(600)
    
    # Inform the Agent and Platform server that this application can do tasks on the device
    davraSdk.registerCapability('agent-action-ledTurnOn', { \
            "functionParameters": { }, \
            "functionLabel": "Turn on the LED", \
            "functionDescription": "Turn on the LED connected to the device" \
    }, ledTurnOn)
    davraSdk.registerCapability('agent-action-ledTurnOff', { \
            "functionParameters": { }, \
            "functionLabel": "Turn off the LED", \
            "functionDescription": "Turn off the LED connected to the device" \
    }, ledTurnOff)
    davraSdk.registerCapability('agent-action-ledFlash', { \
            "functionParameters": { "LED Duty cycle (secs)": "string" }, \
            "functionLabel": "Flash the LED on and off", \
            "functionDescription": "For the LED connected to the device, set it flashing at a configurable speed" \
    }, ledFlash)
    davraSdk.registerCapability('agent-action-getProcessListing', { \
            "functionParameters": { }, \
            "functionLabel": "Get the list of processes running", \
            "functionDescription": "Get the list of processes running on the device" \
    }, getProcessListing)

    # Demonstration of how to listen to any communication on the device (the agent or other apps)
    davraSdk.listenToAllMessagesFromAgent(onAnyMessageReceived)

    # Demonstration of how to send a miscellaneous message to the agent
    davraSdk.sendMessageFromAppToAgent({"message": "test from app"})

    # Main loop to run forever. 
    countMainLoop = 0
    # Demonstration of sending alarm event from app to server via agent
    davraSdk.sendIotData({"name": "davranetworks.alarm", "msg_type": "event", \
    "value": {"message": "sampleAppLed started", "severity": "INFO", "config": { "name": "sampleAppLed started"}}})

    # Demonstration of sending event from app to server via agent
    davraSdk.sendIotData({"name": "sampleAppledOn", "msg_type": "event", \
    "value": {"message": "Led turned on", "severity": "INFO", "config": { "name": "sampleAppledOn"}}})

    while True:
        # Only every n seconds
        if(countMainLoop % 60 == 0):
            davraSdk.log('Application running: ' + appConfig["applicationName"])
        if(countMainLoop % 120 == 0):
            davraSdk.sendMetricValue("counter", countMainLoop)
        # If the LED was set to flash on and off
        if(ledDutyCycle != -1):
            if((countMainLoop / ledDutyCycle) % 2 == 0):
                GPIO.output(27, GPIO.LOW)
            else:
                GPIO.output(27, GPIO.HIGH)
        # Loop once per second
        countMainLoop += 1
        time.sleep(1)
# End Main loop