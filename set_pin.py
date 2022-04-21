import paho.mqtt.client as mqtt
import time
import serial

#def set_io(pin_number,level):
  #client = mqtt.Client(client_id="set-pin")
  #client.username_pw_set(username="digi-hw",password="tegut")
  #client.connect("frackles")
  #client.publish("digi/set_io","{} {}".format(pin_number,level))
  
def set_io(pin_number,level):
  with serial.Serial('/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0', 115200) as ser:
    ser.write("{} {}\n".format(pin_number,level).encode())
    print("setting pin " + str(pin_number) + " " + level + "\n")

def enable_clock():
  set_io(4,'on')

def disable_clock():
  set_io(4,'off')

def start_reset():
  set_io(3,'on')

def stop_reset():
  set_io(3,'off')

if __name__=='__main__':
  time.sleep(10)
  enable_clock()
  time.sleep(1)
  disable_clock()
