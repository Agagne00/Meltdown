import RPi.GPIO as GPIO
from tkinter import *
import time
import random
import threading
import inputs

random.seed(time.time())

joySW=37
joyY=38
joyX=40
touchSensor=36
blueButton=33
reedSensor=32
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)


       
buzzer=3
LED_R=10
LED_G=8
LED_B=5
segments=[23,24,11,15,29,31,13,26]
digits=[21,22,19,18]

num = {' ':(0,0,0,0,0,0,0), #pins start at top left and progress clockwise, then middle
       0:(1,1,1,1,1,1,0),
       1:(0,0,1,1,0,0,0),
       2:(0,1,1,0,1,1,1),
       3:(0,1,1,1,1,0,1),
       4:(1,0,1,1,0,0,1),
       5:(1,1,0,1,1,0,1),
       6:(1,1,0,1,1,1,1),
       7:(0,1,1,1,0,0,0),
       8:(1,1,1,1,1,1,1),
       9:(1,1,1,1,1,0,1)}

GPIO_TL = {37:"Joystick In",
           38:"Joystick Right",
           40:"Joystick Up",
           36:"Touch Sensor",
           33:"Potentiometer",
           32:"Reed Sensor"}

masterInputs = [[],[],[],[],[],[]] #one list for each element, containing device, button code, and button name.
buttons = open("inputLog.txt","r")
buttons.readline()
for i in masterInputs:
    i.append(buttons.readline().strip()) #input device
    i.append(buttons.readline().strip()) #input device name
    buttons.readline() # skip over "Key"
    i.append(int(buttons.readline().strip())) #event code. button code/GPIO pin
    if i[0] == "GPIO":
        i.append(GPIO_TL[i[2]])
    else:
        i.append(str(i[2])) # add button code as a string for rules parsing.  I think this is already a string, but whatever.
    buttons.readline() # skip over 1
buttons.close()
#masterInputs = [["GPIO","GPIO",37,"Joystick In"],["GPIO","GPIO",38,"Joystick Right"],["GPIO","GPIO",40,"Joystick Up"],["GPIO","GPIO",36,"Touch Sensor"],["GPIO","GPIO",33,"Potentiometer"],["GPIO","GPIO",32,"Reed Sensor"]]

usingKey=0;usingGamepad=0;usingGPIO=0;usingMouse=0
for i in masterInputs:
    if i[0]=="GPIO":
        usingGPIO=1
    if i[0]=="Gamepad":
        usingGamepad=1
    if i[0]=="Keyboard":
        usingKey=1
    if i[0]=="Mouse":
        usingMouse=1

## add on all the GUI inputs
masterInputs.append(["GUI",0,0,"Vent Vespene Gas"])
masterInputs.append(["GUI",0,0,"Ignite Plasma Array"])
masterInputs.append(["GUI",0,0,"Arm Aerial Drones"])
masterInputs.append(["GUI",0,0,"increase Radiation Intensity until it stops"])


masterOutputs = [["segmentLeft","the left two digits exceed 50"], ["segmentRight","the right two digits are below 50"], ["lowBuzzer","you hear a slow buzzer"], ["highBuzzer","you hear a fast buzzer"], ["LEDR","you see a red LED"], ["LEDG","you see a green LED"], ["LEDB","you see a blue LED"], ["monkey","the monkeys get rowdy (over 100)"]]
## OKAY, turns out python REALLY dislikes functions as args, so each one will be replaced by a string and checked later.

gameOver=0
class MeltdownGUI:
    def __init__(self):
        self.start=0
        self.digits=[0,0,0,0]
        self.danger=0
        self.redLight=0
        self.greenLight=0
        self.blueLight=0
        self.monkeys=0
        self.lowBuzzer=0
        self.highBuzzer=0
        self.monkey=0
        self.cooldown=[0,0,0,0,0,0,0,0]
        self.inputs = []
        self.outputs = []
        self.rules=[]
        self.possibleInputs=masterInputs.copy()
        self.possibleOutputs=masterOutputs.copy()
        self.bigInputList=[] #this will be filled with zeroes, and the threaded input-getting functions will change them to indicate that a button is pushed.
        
        ## cooldown prevents the same problem from activating twice in quick succession.  An input and output are disabled for a time after a correct press.
        ## cooldown represents, in order: segmentLeft, segmentRight, lowBuzzer, highBuzzer, redLight, greenLight, blueLight, monkeys.
        self.loop=-1000 ## this increments every ~10ms, to decide game logic
        
        self.main_window=Tk()
        self.main_window.geometry("500x400+100+100")
        self.main_window.title("Meltdown")

        
        self.frame1 = Frame(self.main_window)
        self.titleLabel1 = Label(self.frame1,text="Meltdown",font=("Arial",32))
        self.titleLabel1.grid(row=0,column=0,columnspan=2)
        self.rulesLabel = Label(self.frame1,text="Number of rules:",font=("Arial",16))
        self.rulesLabel.grid(row=1,column=0)
        self.rulesSelect = Spinbox(self.frame1,from_=0,to_=8,font=("Arial",16),width=10,state="readonly")
        self.rulesSelect.grid(row=1,column=1)
        self.startButton = Button(self.frame1,text="Start Game",font=("Arial",16),command=self.makeGame)
        self.startButton.grid(row=2,column=0)
        self.quitButton = Button(self.frame1,text="Quit",font=("Arial",16),command=self.main_window.destroy)
        self.quitButton.grid(row=2,column=1)
        self.frame1.grid()
        #frame 2 is the general game frame.  All the game stuff happens here.
        self.frame2 = Frame(self.main_window)
        self.titleLabel2 = Label(self.frame2,text="Meltdown",font=("Arial",32))
        self.titleLabel2.grid(row=0,column=0,columnspan=2)
        self.dangerLabel = Label(self.frame2,text="Danger Level:",font=("Arial",16),fg="Red")
        self.dangerLabel.grid(row=2,column=0)
        self.timer = IntVar()
        self.timerLabel = Label(self.frame2,textvariable=self.timer,font=("Arial",24))
        self.timerLabel.grid(row=1,column=1)
        self.timeLeftLabel = Label(self.frame2,text="Time left:",font=("Arial",16))
        self.timeLeftLabel.grid(row=1,column=0)
        self.dangerBG = Label(self.frame2,bg="White",height=3,width=30,fg="red2")
        self.dangerBG.grid(row=2,column=1, padx=10)
        self.inputScaleLabel = Label(self.frame2,text="Radiation Intensity:",font=("Arial",16))
        self.inputScaleLabel.grid(row=4,column=0)
        self.inputScale = Scale(self.frame2,from_=0,to_=100,orient=HORIZONTAL,command=self.radiationTranslate)
        self.inputScale.grid(row=5,column=0)
        self.monkeyLabel = Label(self.frame2,text="Monkey Ferocity:",font=("Arial",16))
        self.monkeyLabel.grid(row=4,column=1)
        self.monkeyCountLabel = Label(self.frame2,text="Very",font=("Arial",16))
        self.monkeyCountLabel.grid(row=5,column=1)
        self.rbValue = IntVar()
        self.rb1 = Radiobutton(self.frame2,text="Off",font=("Arial",16),variable=self.rbValue,value=0,command=self.rbTranslate)
        self.rb1.grid(row=6,column=0)
        self.rb2 = Radiobutton(self.frame2,text="Ignite Plasma Array",font=("Arial",16),variable=self.rbValue,value=1,command=self.rbTranslate)
        self.rb2.grid(row=7,column=0)
        self.rb3 = Radiobutton(self.frame2,text="Arm Aerial Drones",font=("Arial",16),variable=self.rbValue,value=2,command=self.rbTranslate)
        self.rb3.grid(row=8,column=0)
        self.ventButton = Button(self.frame2,text="Vent Vespene Gas",font=("Arial",20),command=self.vent)
        self.ventButton.bind("<ButtonRelease>",self.unvent)
        self.ventButton.grid(row=6,column=1,rowspan=2)
        self.updateButton = Button(self.frame2,text="Update",font=("Arial",16),command=self.updateGUI)
        self.updateButton.grid(row=8,column=1)

        #frame3 is the endscreen, showing the basic game stats (time left, danger level, danger color) and whether they won.
        #update to appropriate values with config in endGame()
        self.frame3 = Frame(self.main_window)
        self.titleLabel3 = Label(self.frame3,text="Meltdown",font=("Arial",32))
        self.titleLabel3.grid(row=0,column=0,columnspan=2)
        self.fanfareLabel1 = Label(self.frame3,text="You successfully contained the meltdown.",font=("Arial",16))
        self.fanfareLabel1.grid(row=1,column=0)
        self.fanfareLabel2 = Label(self.frame3,text="Time left: ",font=("Arial",16))
        self.fanfareLabel2.grid(row=2,column=0,pady=10)
        self.fanfareLabel3 = Label(self.frame3,text="Rules: ",font=("Arial",16))
        self.fanfareLabel3.grid(row=3,column=0,pady=10)
        self.fanfareLabel4 = Label(self.frame3,text="Danger level: ",font=("Arial",16))
        self.fanfareLabel4.grid(row=4,column=0,pady=10)
        self.fanfareLabel5 = Label(self.frame3,text="Danger code: ",font=("Arial",16))
        self.fanfareLabel5.grid(row=5,column=0,pady=10)
        self.restartButton = Button(self.frame3,text="New Game",font=("Arial",16),command=self.restart)
        self.restartButton.grid(row=6,column=0)

        self.frame4 = Frame(self.main_window)
        self.canvas = Canvas(self.frame4,width=500,height=400,bg="Black")
        self.canvas.grid()
        self.explode=PhotoImage(file="Explosion-PNG.png")
        self.boom=self.explode.subsample(2,2)
        self.canvas.create_image(0,0,anchor=NW,image=self.boom)
        self.escape = Button(self.frame4,text="GAME OVER",font=("Arial",16),bg="Black",fg="Red",command=self.endScreen)
        self.escape.place(x=350,y=300)

    def endScreen(self):
        self.frame4.grid_forget()
        self.frame3.grid()
    def restart(self):
        self.frame3.grid_forget()
        self.frame1.grid()
    def updateGUI(self):
        ## set dangerBG color, show monkey ferocity, and show exact Danger level on dangerBG, and update timer
        global gameOver
        self.timer.set((6000-self.loop)//100)
        self.dangerBG.config(text=str(self.danger))
        self.monkeyCountLabel.config(text=str(self.monkeys))
        if self.danger<=2000:
            self.dangerBG.config(bg="White")
        elif self.danger<=4000:
            self.dangerBG.config(bg="Green")
        elif self.danger<=6000:
            self.dangerBG.config(bg="Yellow")
        elif self.danger<=8000:
            self.dangerBG.config(bg="Orange")
        elif self.danger<=9000:
            self.dangerBG.config(bg="Red")
            self.dangerBG.config(fg="Black")
        else:
            self.dangerBG.config(bg="Black")
            self.dangerBG.config(fg="Red")
        if gameOver:
            self.endGame()
        if self.loop>=60000:
            gameOver=2
            self.endGame()
    def radiationTranslate(self,a):
        for x in range(len(self.inputs)):
            if self.inputs[x][3]=="increase Radiation Intensity until it stops":
                if self.inputScale.get() >= 50:
                    self.bigInputList[x]=1
                else:
                    self.bigInputList[x]=0
    def rbTranslate(self):
        for x in range(len(self.inputs)):
            if self.inputs[x][3]=="Arm Aerial Drones":
                if self.rbValue.get()==2:
                    self.bigInputList[x]=1
                else:
                    self.bigInputList[x]=0
            if self.inputs[x][3]=="Ignite Plasma Array":
                if self.rbValue.get()==1:
                    self.bigInputList[x]=1
                else:
                    self.bigInputList[x]=0
    def vent(self):
        for x in range(len(self.inputs)):
            if self.inputs[x][3]=="Vent Vespene Gas":
                self.bigInputList[x]=1
    def unvent(self,a):
        for x in range(len(self.inputs)):
            if self.inputs[x][3]=="Vent Vespene Gas":
                self.bigInputList[x]=0

    def endGame(self):
        self.fanfareLabel2.config(text="Time left: " + str((6000-self.loop)//100))
        self.fanfareLabel3.config(text="Rules: " + str(self.rulesSelect.get()))
        if gameOver==2:
            print("You are a winner!")
            self.fanfareLabel1.config(text="You successfully contained the meltdown.")
            self.fanfareLabel4.config(text="Danger level: " + str(self.danger))
            if self.danger<=2000:
                self.fanfareLabel5.config(text="Danger code: White")
            elif self.danger<=4000:
                self.fanfareLabel5.config(text="Danger code: Green")
            elif self.danger<=6000:
                self.fanfareLabel5.config(text="Danger code: Yellow")
            elif self.danger<=8000:
                self.fanfareLabel5.config(text="Danger code: Orange")
            elif self.danger<=9000:
                self.fanfareLabel5.config(text="Danger code: Red")
            else:
                self.fanfareLabel5.config(text="Danger code: Black")
            self.frame2.grid_forget()
            self.frame3.grid()
            GPIO.output(redLight,0)
            GPIO.output(greenLight,0)
            GPIO.output(blueLight,0)
            GPIO.output(buzzer,0)
            for pin in segments:
                GPIO.output(pin,0)
        elif gameOver==1:
            self.fanfareLabel1.config(text="You failed to contain the meltdown.")
            self.fanfareLabel4.config(text="Danger level: 10000")
            self.fanfareLabel5.config(text="Danger code: MELTDOWN")
            ## display a canvas with Explosion-PNG on it, wait 3 seconds, then go to frame3
            self.frame2.grid_forget()
            self.frame4.grid()
    def setDangerColor(self):
        global gameOver
        if self.danger ==2000:
            print("Danger level elevated to Green.")
        elif self.danger==4000:
            print("Danger level elevated to Yellow.  Be careful.")
        elif self.danger==6000:
            print("Danger level elevated to Orange.  What's going on over there?")
        elif self.danger==8000:
            print("Danger level elevated to Red.  Extreme danger!")
        elif self.danger==9000:
            print("DANGER LEVEL ELEVATED TO BLACK.  MELTDOWN IMMINENT.")
        elif self.danger>=10000 and gameOver==0:
            gameOver=1
    
                
            
    def segmentLeftUpdate(self,press):
        # if press, then associated button is being pressed.  If so, return true.  If not return false.
        if self.cooldown[0]==0:
            if press and self.digits[0] > 4:
                self.digits[0]=0
                self.digits[1]=random.randint(0,9)
                self.cooldown[2]=200
            elif press:
                self.danger+=10
            elif self.digits[0] > 4:
                self.danger+=1
            number = self.digits[0]*10+self.digits[1]
            number+=random.randint(0,5)
            if number>99:
                number=99
            if self.loop%50==0:
                self.digits[1]=number%10
                self.digits[0]=number//10
        else:
            self.cooldown[0]-=1
    def segmentRightUpdate(self,press):
        # remember, a separate function will actually update behavior for all output devices.
        if self.cooldown[1]==0:
            if press and self.digits[2] < 5:
                self.digits[2]=9
                self.digits[3]=random.randint(0,9)
                self.cooldown[2]=200
            elif press:
                self.danger+=10
            elif self.digits[2] < 5:
                self.danger+=1
            number = self.digits[2]*10+self.digits[3]
            number-=random.randint(0,5)
            if number<0:
                number=0
            if self.loop%50==0:
                self.digits[3]=number%10
                self.digits[2]=number//10
        else:
            self.cooldown[1]-=1
    def lowBuzzerUpdate(self,press):
        ## let's say that two seconds (200 loop rotations), a new value is tossed to lowBuzzer and highBuzzer, from 0 to 9, and if they are exactly 0 then they turn on and stay on.
        if self.cooldown[2]==0:
            if self.lowBuzzer==9 and press:
                self.lowBuzzer=1
                self.cooldown[2]=200
            elif press:
                self.danger+=10
            elif self.lowBuzzer==9:
                self.danger+=1
            elif self.loop%200==0:
                self.lowBuzzer=random.randint(4,9)
        else:
            self.cooldown[2]-=1
    def highBuzzerUpdate(self,press):
        if self.cooldown[3]==0:
            if self.highBuzzer==9 and press:
                self.highBuzzer=1
                self.cooldown[3]=200
            elif press:
                self.danger+=10
            elif self.highBuzzer==9:
                self.danger+=1
            elif self.loop%200==0:
                self.highBuzzer=random.randint(4,9)
        else:
            self.cooldown[3]-=1
    def LEDRUpdate(self,press):
        if self.cooldown[4]==0:
            if self.redLight==9 and press:
                self.redLight=0
                self.cooldown[4]=200
            elif press:
                self.danger+=10
            elif self.redLight==9:
                self.danger+=1
            elif self.loop%200==0:
                self.redLight=random.randint(4,9)
        else:
            self.cooldown[4]-=1
    def LEDGUpdate(self,press):
        if self.cooldown[5]==0:
            if self.greenLight==9 and press:
                self.greenLight=0
                self.cooldown[5]=200
            elif press:
                self.danger+=10
            elif self.greenLight==9:
                self.danger+=1
            elif self.loop%200==0:
                self.greenLight=random.randint(4,9)
        else:
            self.cooldown[5]-=1
    def LEDBUpdate(self,press):
        if self.cooldown[6]==0:
            if self.blueLight==9 and press:
                self.blueLight=0
                self.cooldown[6]=200
            elif press:
                self.danger+=10
            elif self.blueLight==9:
                self.danger+=1
            elif self.loop%200==0:
                self.blueLight=random.randint(4,9)
        else:
            self.cooldown[6]-=1
    def monkeyUpdate(self,press):
        if self.cooldown[7]==0:
            if self.monkeys>=100 and press:
                self.monkeys-=100
                self.monkeys-=random.randint(10,20)
            elif press:
                self.danger+=10
            elif self.monkeys>=100:
                self.danger+=1
                if self.loop%50==0 and self.monkeys>=150: ## message waits until 150 to reward the player for smashing the Update button, that's good game design baby
                    print("These monkeys are getting out of control! Do something!")
            elif self.loop%100==0:
                self.monkeys+=random.randint(0,25)
        else:
            self.cooldown[7]-=1
    def realOutputUpdate(self,b):
        ## update digits for GPIO
        if self.loop%200<100:
            b.ChangeDutyCycle((self.lowBuzzer==9))
        else:
            b.ChangeDutyCycle((self.highBuzzer==9)*50)
        GPIO.output(LED_R,self.redLight==9)
        GPIO.output(LED_G,self.greenLight==9)
        GPIO.output(LED_B,self.blueLight==9)
    def getInputs(self):
        #for now we'll assume we are only getting GPIO inputs.  otherwise i'd make a separate thread and function for each input device.
        global gameOver
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(joySW,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(joyY,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(joyX,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(touchSensor,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(blueButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        GPIO.setup(reedSensor,GPIO.IN,pull_up_down=GPIO.PUD_UP)
        while True:
            if gameOver>0:
                return
            joyIn = GPIO.input(joySW) == GPIO.LOW
            joyYIn = GPIO.input(joyY) == GPIO.LOW
            joyXIn = GPIO.input(joyX) == GPIO.LOW
            touchIn = GPIO.input(touchSensor) == GPIO.HIGH
            blueIn = GPIO.input(blueButton) == GPIO.LOW
            reedIn=GPIO.input(reedSensor) == GPIO.HIGH
            # need to flip the touch sensor and reed sensor since they're wrong
            inputList=[joyIn,joyYIn,joyXIn,touchIn,blueIn,reedIn]
            pinList=[37,38,40,36,33,32]
            for x in range(len(self.inputs)):
                if self.inputs[x][0] == "GPIO":
                    # check the pin
                    for i in range(len(pinList)):
                        if pinList[i] == self.inputs[x][2]:
                           self.bigInputList[x] = inputList[i]
    def getInputsKey(self):
        global gameOver
        while True:
            if gameOver>0:
                return
            events = inputs.get_key()
            for x in range(len(self.inputs)):
                for y in range(0,8): ## only check the 8 latest events from earliest to latest, of which 4 are system things.  Essentially can handle 2-3 buttons in and out at once.
                    if self.inputs[x][0] == "Gamepad" and self.inputs[x][1] == events[y].device.name and self.inputs[x][2]==events[y].code:
                        self.bigInputList[x]=events[y].state
                    
    def getInputsMouse(self):
        global gameOver
        while True:
            if gameOver>0:
                return
            events = inputs.get_mouse()
            for x in range(len(self.inputs)):
                for y in range(0,8): ## only check the 8 latest events from earliest to latest, of which 4 are system things.  Essentially can handle 2-3 buttons in and out at once.
                    if self.inputs[x][0] == "Gamepad" and self.inputs[x][1] == events[y].device.name and self.inputs[x][2]==events[y].code:
                        self.bigInputList[x]=events[y].state
    def getInputsGamepad(self):
        global gameOver
        while True:
            if gameOver>0:
                return
            events = inputs.get_gamepad()
            for x in range(len(self.inputs)):
                for y in range(0,8): ## only check the 8 latest events from earliest to latest, of which 4 are system things.  Essentially can handle 2-3 buttons in and out at once.
                    if len(events)>=y+1:
                        if self.inputs[x][0] == "Gamepad" and self.inputs[x][1] == events[y].device.name and self.inputs[x][2]==events[y].code:
                            self.bigInputList[x]=events[y].state
    def doOutputs(self):
        global gameOver
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(buzzer,GPIO.OUT)
        b = GPIO.PWM(buzzer,20)
        b.start(0)
        GPIO.setup(LED_R,GPIO.OUT)
        GPIO.setup(LED_G,GPIO.OUT)
        GPIO.setup(LED_B,GPIO.OUT)
        for pin in segments:
            GPIO.setup(pin,GPIO.OUT)
        for pin in digits:
            GPIO.setup(pin,GPIO.OUT)
        while True:
            if self.loop<0:
                self.loop+=1
                time.sleep(0.005)
            else:
                if gameOver>0:
                    break
                for x in range(len(self.outputs)):
                    nextIn = self.bigInputList[x]
                    if self.outputs[x][0]=="segmentLeft":
                        self.segmentLeftUpdate(nextIn)
                    elif self.outputs[x][0]=="segmentRight":
                        self.segmentRightUpdate(nextIn)
                    elif self.outputs[x][0]=="lowBuzzer":
                        self.lowBuzzerUpdate(nextIn)
                    elif self.outputs[x][0]=="highBuzzer":
                        self.highBuzzerUpdate(nextIn)
                    elif self.outputs[x][0]=="LEDR":
                        self.LEDRUpdate(nextIn)
                    elif self.outputs[x][0]=="LEDG":
                        self.LEDGUpdate(nextIn)
                    elif self.outputs[x][0]=="LEDB":
                        self.LEDBUpdate(nextIn)
                    elif self.outputs[x][0]=="monkey":
                        self.monkeyUpdate(nextIn)

                for digit in range(4):
                    for loop in range(0,7):
                        GPIO.output(segments[loop],num[self.digits[digit]][loop])
                    GPIO.output(digits[digit],0)
                    time.sleep(0.0005)
                    GPIO.output(digits[digit],1)
                self.setDangerColor()
                self.realOutputUpdate(b)
                self.loop+=1
                if self.loop>=60000 and gameOver==0:
                    gameOver=2
            time.sleep(0.000) #should be .008 to match the loop, but doOutputs is REALLY slow right now.
    def makeGame(self):
        global gameOver,usingKey,usingMouse,usingGPIO,usingGamepad
        gameOver=0
        self.start=time.time()
        self.digits=[0,0,0,0]
        self.loop=-1000
        self.danger=0
        self.redLight=0
        self.greenLight=0
        self.blueLight=0
        self.monkeys=0
        self.lowBuzzer=0
        self.highBuzzer=0
        self.monkey=0
        self.cooldown=[0,0,0,0,0,0,0,0]
        self.inputs = []
        self.outputs = []
        self.rules=[]
        self.possibleInputs=masterInputs.copy()
        self.possibleOutputs=masterOutputs.copy()
        self.bigInputList=[]
        self.frame1.grid_forget()
        self.frame2.grid()
        for i in range(int(self.rulesSelect.get())):
            self.inputs.append(self.possibleInputs[random.randint(0,len(self.possibleInputs)-1)])
            self.outputs.append(self.possibleOutputs[random.randint(0,len(self.possibleOutputs)-1)])
            self.possibleInputs.remove(self.inputs[i])
            self.possibleOutputs.remove(self.outputs[i])
            self.rules.append("When " + self.outputs[i][1] + ", press " + self.inputs[i][3] + ".")
            self.bigInputList.append(0)
        #start listening on inputDevice inputs (or all inputs if threading)
        # possibly a separate thread for each input???  For now, just do it normally.
        print(self.rules)
        self.rulesWindow = Toplevel() ## this may or may not work
        self.rulesWindow.geometry("250x400+600+100") #Maybe too small for 8 rules? If so, adjust font
        ruleText=""
        for x in range(len(self.rules)):
            ruleText=ruleText+ "Rule #" + str(x+1) + ": " + self.rules[x] + "\n"
        self.rWindowRules = Label(self.rulesWindow,text=ruleText,font=("Arial",12),justify=CENTER,wraplength=250)
        self.rWindowRules.grid() #toy with wraplength value if it doesn't work
        #show rules in a separate window or something, then pause for 10 seconds to take in the rules.
        print("Here's your manual.  Your shift starts in 10 seconds.  Good luck.")
        if usingGPIO:
            gameInput = threading.Thread(target=self.getInputs,daemon=True)
            gameInput.start()
        if usingKey:
            gameInput2 = threading.Thread(target=self.getInputsKey,daemon=True)
            gameInput2.start()
        if usingMouse:
            gameInput3 = threading.Thread(target=self.getInputsMouse,daemon=True)
            gameInput3.start()
        if usingGamepad:
            gameInput4 = threading.Thread(target=self.getInputsGamepad,daemon=True)
            gameInput4.start()
        gameOutput = threading.Thread(target=self.doOutputs,daemon=True)
        gameOutput.start()

m=MeltdownGUI()
GPIO.cleanup()
