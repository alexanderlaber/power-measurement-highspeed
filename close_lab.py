import paho.mqtt.client as mqtt

def close_lab(system_code, unit_code):
  client = mqtt.Client(client_id="hello")
  client.username_pw_set(username="digi-hw",password="tegut")
  client.connect("frackles")
  #client.publish("digi/433","11111 10000 off")
  client.publish("digi/433",f"{system_code} {unit_code} off")


if __name__=='__main__':
  close_lab("11111", "10101")
