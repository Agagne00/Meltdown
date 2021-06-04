import RPi.GPIO as GPIO
import inputs
import time

joySW=37
joyY=38
joyX=40
touchSensor=36
blueButton=33
reedSensor=32
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(joySW,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(joyY,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(joyX,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(touchSensor,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(blueButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(reedSensor,GPIO.IN,pull_up_down=GPIO.PUD_UP)

INPUT_DEVICES = ["potentiometer","reed sensor","touch sensor","joystick up","joystick right","joystick in"]
iDevices = ["Keyboard","Mouse","GPIO","Gamepad"]
INPUT_LOGS = [[],[],[],[],[],[]]

print("Enter the specified buttons in order.  To avoid headaches, PLEASE do not set the same button for two functions, OR use the left mouse button for any function.")
print("ONLY press a button when you are told to, and not before.  Pressing too many buttons leads to aberrant behavior.")

for i in range(len(INPUT_DEVICES)):
    print("Button #" + str(i) + ".  Default:" + INPUT_DEVICES[i])
    iDevice=int(input("Choose an input device.  Keyboard=0, Mouse=1, GPIO=2, Gamepad=3\n"))
    while int(iDevice) < 0 or int(iDevice) > 3:
        iDevice=input("Error: choose a valid number")
    print("Press the button to assign it.")
    while INPUT_LOGS[i] == []:
        events=[]
        if iDevice==2:
            if GPIO.input(joySW)==GPIO.LOW:
                print(iDevices[iDevice], "GPIO", "Key", joySW, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", joySW, "1"]
            if GPIO.input(joyY)==GPIO.LOW:
                print(iDevices[iDevice], "GPIO", "Key", joyY, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", joyY, "1"]
            if GPIO.input(joyX)==GPIO.LOW:
                print(iDevices[iDevice], "GPIO", "Key", joyX, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", joyX, "1"]
            if GPIO.input(touchSensor)==GPIO.HIGH:
                print(iDevices[iDevice], "GPIO", "Key", touchSensor, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", touchSensor, "1"]
            if GPIO.input(blueButton)==GPIO.LOW:
                print(iDevices[iDevice], "GPIO", "Key", blueButton, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", blueButton, "1"]
            if GPIO.input(reedSensor)==GPIO.HIGH:
                print(iDevices[iDevice], "GPIO", "Key", reedSensor, 1)
                INPUT_LOGS[i] = ["GPIO", "GPIO", "Key", reedSensor, "1"]
                    
        else:
            if iDevice==0:
                time.sleep(2)
                events=inputs.get_key()
            elif iDevice==1:
                time.sleep(2)
                events=inputs.get_mouse()
            elif iDevice==3:
                events=inputs.get_gamepad()
            for event in events:
                if event.ev_type=="Key" and event.state==1:
                    print(iDevices[iDevice], event.device, event.ev_type, event.code, event.state)
                    INPUT_LOGS[i]= [iDevices[iDevice], event.device.name, event.ev_type, event.code, event.state]

## save txt log of inputs, to be pulled later.
## perhaps we'll have a potentiometer on the board that can't be altered,
## but can be toggled on/off
f=open("inputLog.txt","w")
f.write("PLEASE do not touch any of this info, unless you KNOW what you're doing!\n")
for log in INPUT_LOGS:
    f.write(log[0]) # Keyboard/Mouse/GPIO/Gamepad
    f.write("\n")
    f.write(log[1]) # event device name, to check which device
    f.write("\n")
    f.write(log[2]) # event type, always Key
    f.write("\n")
    f.write(str(log[3])) # event code, corresponds to which key pressed OR which GPIO port.
    f.write("\n")
    f.write(str(log[4])) # event state, always 1
    f.write("\n")
f.close()    
