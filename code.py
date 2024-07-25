import pandas as pd
from datetime import datetime, timedelta
import random
import string
import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time
from twilio.rest import Client

#Give your Twilio ID and Token Here
#account_sid =
#auth_token =
client = Client(account_sid, auth_token)

C1 = 32
C2 = 36
C3 = 38
C4 = 40

L1 = 31
L2 = 33
L3 = 35
L4 = 37

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

GPIO.setup(L1, GPIO.OUT)
GPIO.setup(L2, GPIO.OUT)
GPIO.setup(L3, GPIO.OUT)
GPIO.setup(L4, GPIO.OUT)

GPIO.setup(C1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C3, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(C4, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

servo_pin = 12
GPIO.setup(servo_pin, GPIO.OUT)

GPIO.setup(16, GPIO.OUT)
GPIO.setup(18, GPIO.OUT)

lcd = CharLCD('PCF8574', 0x27)

db = pd.DataFrame(columns = ['car_number', 'phone', 'entry_time', 'otp', 'in_garage', 'total_seconds', 'slot'])

def csv_read():
    global db
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:

rows = 2
cols = 2
slots = rows * cols
slot_names = []
for r in range(rows):
  for c in range(cols):
    slot_names.append(f"{chr(65+r)}{c+1}")

def readLine(line, characters):
    ch = ''
    GPIO.output(line, GPIO.HIGH)
    if(GPIO.input(C1) == 1):
        ch = characters[0]
    if(GPIO.input(C2) == 1):
        ch = characters[1]
    if(GPIO.input(C3) == 1):
        ch = characters[2]
    if(GPIO.input(C4) == 1):
        ch = characters[3]
    GPIO.output(line, GPIO.LOW)
    return ch

def input(n, l):
  lcd.clear()
  lcd.cursor_pos = (0, 0)
  lcd.write_string(l)
  lcd.cursor_pos = (1, 0)
  s = ""
  while len(s) < n:
      t = ""
      t += readLine(L1, ["1","2","3","A"])
      t += readLine(L2, ["4","5","6","B"])
      t += readLine(L3, ["7","8","9","C"])
      t += readLine(L4, ["Y","0","N",""])
      if(len(t) > 0):
          lcd.cursor_pos = (1, 0)
          lcd.write_string("            ")
          lcd.cursor_pos = (1, 0)
          if(t == 'A'):
              print(s)
              return s
          elif(t == 'B'):
              if(len(s) > 0):
                s = s[0: len(s) - 1]
                print(s)
          elif(t == 'C'):
              print(s, end = "\nString reset")
              s = ""
          else:
              s += t
              print(s)
          lcd.write_string(s)
      time.sleep(0.2)
  return s

def send_sms(body, to_number):
  message = client.messages.create(
  body = body,
  from_=#Your Twilio Number,
  to = to_number)

def generate_otp():
  return random.randint(1000, 9999)

def send_otp(otp, phone_number):
  message = client.messages.create(
  body = f"Your OTP for {datetime.today().date()} is {otp}",
  from_= #Your Twilio Number,
  to = phone_number)
  print(f"OTP sent to {phone_number}")

def str2time(tim):
  parts = tim.split(' ')
  date = parts[0]
  time = parts[1]
  datep = date.split('-')
  yr = int(datep[0])
  mo = int(datep[1])
  day = int(datep[2])
  timep = time.split(':')
  hr = int(timep[0])
  mi = int(timep[1])
  sec = float(timep[2])

def motor(sl):
  if(sl == 'A1'):
    GPIO.output(16, GPIO.LOW)
    GPIO.output(18, GPIO.LOW)
  elif(sl == 'A2'):
    GPIO.output(16, GPIO.HIGH)
    GPIO.output(18, GPIO.LOW)
  elif(sl == 'B1'):
    GPIO.output(16, GPIO.LOW)
    GPIO.output(18, GPIO.HIGH)
  elif(sl == 'B2'):
    GPIO.output(16, GPIO.HIGH)
    GPIO.output(18, GPIO.HIGH)
  
  servo_pwm = GPIO.PWM(servo_pin, 50)
  servo_pwm.start(2.0)
  time.sleep(2)
  servo_pwm.ChangeDutyCycle(7.0)
  time.sleep(2)
  servo_pwm.ChangeDutyCycle(2.0)
  time.sleep(2)
  servo_pwm.stop()

def add_car(car_number):
    global db
    if(car_number in db['car_number'].unique()):
      entry = db[(db['car_number'] == car_number)]
      phone_number = "+"+str(entry['phone'].values[0])
      print("Present number: ", phone_number)
      x = input(1, "Keep same number ? y/n").lower()
      while(x != 'y' and x != 'n'):
        x = input(1, "Wrong Input !! Try again : ").lower()
      if(x == 'n'):
        phone_number = "+91" + input(10, "Enter new phone number")
      if(entry['in_garage'].values[0] == 1):
        print("Car already in garage")
        return
    else:
      phone_number = "+91" + input(10, "Enter phone number: ")
    otp = generate_otp()
    send_otp(otp, phone_number)
    sorted_slots = []
    for r in range(rows):
      for c in range(cols):
        sorted_slots.append(f"{chr(65+r)}{c+1}")
    sl = None
    for slot in sorted_slots:
        if slot not in db['slot'].values:
            sl = slot
            break
    if sl is None:
        print("No available slots.")
        return
    if car_number in db['car_number'].unique():
      db.loc[(db['car_number'] == car_number), 'in_garage'] = 1
      db.loc[(db['car_number'] == car_number), 'slot'] = sl
      db.loc[(db['car_number'] == car_number), 'otp'] = otp
      db.loc[(db['car_number'] == car_number), 'entry_time'] = datetime.now()
      db.loc[(db['car_number'] == car_number), 'phone'] = phone_number;
    else:
      new_row={'car_number':car_number, 'phone':phone_number, 'entry_time':datetime.now(), 'otp':otp, 'in_garage': 1, 'slot':sl, 'total_seconds':0}
      db = db.append(new_row, ignore_index=True)
    db['entry_time'] = pd.to_datetime(db['entry_time'], format='%Y-%m-%d %H:%M:%S')
    print(f"Car {car_number} allotted slot {sl}. OTP sent to {phone_number}")
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string("OTP sent")
    lcd.cursor_pos = (1, 0)
    disp_str = str(sl) + "slot alloted"
    lcd.write_string(disp_str)
    motor(sl)
    db.to_csv("Data.csv", index = False)

def remove_car(car_number):
    global db
    f=0
    for x in db['car_number'].unique():
      if(car_number == int(x)):
        f=1
        break
    if(f == 0):
      print("Car not found")
      return
    entry = db[(db['car_number'] == car_number)]
    print(int(entry['in_garage'].values[0]))
    if(int(entry['in_garage'].values[0]) == 0):
      print("Car not in garage")
      return
    req_otp = entry['otp'].values[0]
    sl = entry['slot'].values[0]
    f=0
    otp = int(input(4, "Enter OTP: "))
    for i in range(0,5):
      if req_otp == otp:
        f=1
        break
      print("OTP incorrect")
      if(i < 4):
        otp = int(input("Re-enter OTP: "))
    if(f == 0):
      print("Incorrect OTP entered too many times....Car Locked")
      entry = db[(db['car_number'] == car_number)]
      phone_number = entry['phone'].values[0]
      message = client.messages.create(body = f"Someone is trying to steal your car", from_ = '+16592645664', to = phone_number)
      return
    entry_time_str= (str(entry['entry_time'].iloc[0]).split('.'))[0]
    entry_time_datetime = datetime.strptime(entry_time_str, "%Y-%m-%d %H:%M:%S")
    parked_time = datetime.now() - entry_time_datetime
    parked_secs = parked_time.total_seconds()
    if car_number in db['car_number'].unique():
        prev_seconds = db.loc[db['car_number'] == car_number, 'total_seconds'].iloc[0]
        new_seconds = prev_seconds + parked_secs
    else:
        new_seconds = parked_secs
    db.loc[(db['car_number'] == car_number) & (db['otp'] == otp), 'in_garage'] = 0
    db.loc[(db['car_number'] == car_number) & (db['otp'] == otp), 'total_seconds'] = new_seconds
    db.loc[(db['car_number'] == car_number) & (db['otp'] == otp), 'slot'] = ''
    hours = parked_secs / 3600
    charge = round(hours * 30)
    filtered_row = db[(db['car_number'] == car_number) & (db['otp'] == otp)]
    if not filtered_row.empty:
      slot_value = filtered_row.iloc[0]['slot']
      print(f"Your charge is {charge}")
      disp_str = "Your charde is " + str(charge)
      lcd.write_string(disp_str)
      motor(sl)
    db.to_csv("Data.csv", index = False)

def main():
    global db
    csv_read()

    while True:
      choice = input(1, "1.Enter 2.Exit:")
      if choice == '1':
        car_number = int(input(4, "Enter car number: "))
        add_car(car_number)
      elif choice == '2':
        car_number = int(input(4, "Enter car number: "))
        remove_car(car_number)
      else:
        break

    print("Thank you for using the garage!")
    GPIO.cleanup()
    
if __name__ == "__main__":
    main()