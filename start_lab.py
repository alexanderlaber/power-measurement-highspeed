import paho.mqtt.client as mqtt

def start_lab():
  client = mqtt.Client(client_id="hello")
  client.username_pw_set(username="digi-hw",password="tegut")
  client.connect("frackles")
  client.publish("digi/433","11111 10000 on")


if __name__=='__main__':
  start_lab()
