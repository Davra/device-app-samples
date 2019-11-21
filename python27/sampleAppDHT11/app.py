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
#GPIO.setmode(GPIO.BCM)
#GPIO.setup(27, GPIO.OUT, initial=GPIO.LOW)



# Turn off the LED
def ledTurnOff(functionInfo):
    global ledDutyCycle
    davraSdk.log('App received instruction to Turn Off Led ' + str(functionInfo))
    GPIO.output(27, GPIO.LOW)
    ledDutyCycle = -1
    davraSdk.sendMessageFromAppToAgent({"finishedFunctionOnApp": functionInfo["functionName"], \
    "status": "completed", \
    "response": "Led was turned off" })

class DHT(object):
    DHTLIB_OK = 0
    DHTLIB_ERROR_CHECKSUM = -1
    DHTLIB_ERROR_TIMEOUT = -2
    DHTLIB_INVALID_VALUE = -999
    
    DHTLIB_DHT11_WAKEUP = 0.020#0.018        #18ms
    DHTLIB_TIMEOUT = 0.0001            #100us
    
    humidity = 0
    temperature = 0
    
    def __init__(self,pin):
        self.pin = pin
        self.bits = [0,0,0,0,0]
        GPIO.setmode(GPIO.BOARD)
    #Read DHT sensor, store the original data in bits[]    
    def readSensor(self,pin,wakeupDelay):
        mask = 0x80
        idx = 0
        self.bits = [0,0,0,0,0]
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,GPIO.LOW)
        time.sleep(wakeupDelay)
        GPIO.output(pin,GPIO.HIGH)
        #time.sleep(40*0.000001)
        GPIO.setup(pin,GPIO.IN)
        
        loopCnt = self.DHTLIB_TIMEOUT
        t = time.time()
        while(GPIO.input(pin) == GPIO.LOW):
            if((time.time() - t) > loopCnt):
                #print ("Echo LOW")
                return self.DHTLIB_ERROR_TIMEOUT
        t = time.time()
        while(GPIO.input(pin) == GPIO.HIGH):
            if((time.time() - t) > loopCnt):
                #print ("Echo HIGH")
                return self.DHTLIB_ERROR_TIMEOUT
        for i in range(0,40,1):
            t = time.time()
            while(GPIO.input(pin) == GPIO.LOW):
                if((time.time() - t) > loopCnt):
                    #print ("Data Low %d"%(i))
                    return self.DHTLIB_ERROR_TIMEOUT
            t = time.time()
            while(GPIO.input(pin) == GPIO.HIGH):
                if((time.time() - t) > loopCnt):
                    #print ("Data HIGH %d"%(i))
                    return self.DHTLIB_ERROR_TIMEOUT        
            if((time.time() - t) > 0.00005):    
                self.bits[idx] |= mask
            #print("t : %f"%(time.time()-t))
            mask >>= 1
            if(mask == 0):
                mask = 0x80
                idx += 1    
        #print (self.bits)
        GPIO.setup(pin,GPIO.OUT)
        GPIO.output(pin,GPIO.HIGH)
        return self.DHTLIB_OK
    #Read DHT sensor, analyze the data of temperature and humidity
    def readDHT11(self):
        rv = self.readSensor(self.pin,self.DHTLIB_DHT11_WAKEUP)
        if (rv is not self.DHTLIB_OK):
            self.humidity = self.DHTLIB_INVALID_VALUE
            self.temperature = self.DHTLIB_INVALID_VALUE
            return rv
        self.humidity = self.bits[0]
        self.temperature = self.bits[2] + self.bits[3]*0.1
        sumChk = ((self.bits[0] + self.bits[1] + self.bits[2] + self.bits[3]) & 0xFF)
        if(self.bits[4] is not sumChk):
            return self.DHTLIB_ERROR_CHECKSUM
        return self.DHTLIB_OK


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
    
    # Demonstration of how to listen to any communication on the device (the agent or other apps)
    davraSdk.listenToAllMessagesFromAgent(onAnyMessageReceived)

    # Demonstration of how to send a miscellaneous message to the agent
    davraSdk.sendMessageFromAppToAgent({"message": "test from DHT11 app"})

    # Main loop to run forever. 
    countMainLoop = 0
    # Demonstration of sending alarm event from app to server via agent
    davraSdk.sendIotData({"name": "davranetworks.alarm", "msg_type": "event", \
    "value": {"message": "sampleAppDHT11 started", "severity": "INFO", "config": { "name": "sampleAppDHT11 started"}}})

    dht = DHT(11)
    okCnt = 0
    while True:
        # read the temp and humidity 
        chk = dht.readDHT11()
        if (chk is 0):
            print("chk : %d, \t Humidity : %.2f, \t Temperature : %.2f "%(chk,dht.humidity,dht.temperature))
            if(countMainLoop % 5 == 0):
                davraSdk.sendMetricValue("process.temperature", dht.temperature)
                davraSdk.sendMetricValue("process.humidity", dht.humidity)
        # Only every n seconds
        if(countMainLoop % 60 == 0):
            davraSdk.log('Application running: ' + appConfig["applicationName"])
        # Loop once per second
        countMainLoop += 1
        time.sleep(1)
# End Main loop
