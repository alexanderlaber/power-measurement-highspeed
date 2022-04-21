import paho.mqtt.client as mqtt

def start_lab(system_code, unit_code):
  client = mqtt.Client(client_id="hello")
  client.username_pw_set(username="digi-hw",password="tegut")
  client.connect("frackles")
  #client.publish("digi/433","11111 10000 on")
  client.publish("digi/433",f"{system_code} {unit_code} on")


if __name__=='__main__':
  start_lab("11111", "10101")
