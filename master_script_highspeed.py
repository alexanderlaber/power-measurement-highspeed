import time
import os
import argparse
from start_lab import start_lab as start
from close_lab import close_lab as close
#from adc_measurement import measure as measure_power
#from adc_measurement import measure_serial as measure_all
from program_pynq import program as program
#from measure_temperature import measure_temperature as measure_temperature
#from set_pin import enable_clock as enable_clock
#from set_pin import disable_clock as disable_clock
#from set_pin import start_reset as start_reset
#from set_pin import stop_reset as stop_reset
from matplotlib import pyplot as plt
import numpy as np

shunt_r = 0.05965
gain_factor = 7.0976
samples=2000

def crc16(data : bytearray, offset=0 , length=63):
    dataarray=[]
    for i in range(length):
        dataarray.append((data[i]))
    if data is None or offset < 0 or offset > len(data)- 1 and offset+length > len(data):
        return 0
    crc = 0xFFFF
    for i in range(0, length):
        crc ^= data[offset + i] << 8
        for j in range(0,8):
            if (crc & 0x8000) > 0:
                crc =(crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF

def bytes_to_24bitint(bytes):
  bytearray=[]
  for b in bytes:
    bytearray.append(b)
  full=(((bytearray[0] << 16) | (bytearray[1] << 8) | bytearray[2]) & 0x00FFFFFF)
  return full

def bytes_to_16bitint(lsb,msb):
  full=(((msb << 8) | lsb) & 0xFFFF)
  return full

def measure_serial_bytes(device_id, shunt_r, gain_factor, offset):
  powerarray_ch0=[]
  powerarray_ch1=[]
  with serial.Serial(device_id, 115200) as ser:
    arduinoreadyarray = [None, None, None, None, None]
    readIdx = 0
    while True:
      newByte = ser.read(1)
      arduinoreadyarray[readIdx] = newByte
      readIdx += 1
      if readIdx == 5:
          readIdx = 0
      arduinoRdy = False
      for offset in range(5):
          if arduinoreadyarray[(0+offset) % 5] == b'r' and arduinoreadyarray[(1+offset) % 5] == b'e' and arduinoreadyarray[(2+offset) % 5] == b'a' and \
                  arduinoreadyarray[(3+offset) % 5] == b'd' and arduinoreadyarray[(4+offset) % 5] == b'y':
            arduinoRdy = True
            break
      if arduinoRdy:
          print("________________________________________")
          print("received ready signal from arduino...")
          print("arduino is ready...")
          break
      else:
        print(f"arduino is not ready ({arduinoreadyarray})")
    ser.write('z'.encode('utf-8'))  #'z'.encode('utf-8')
    print("send go command to arduino...")
    print("receiving data...")

    packetcheckarray=[]
    serial_crc_checkarray = []
    spi_crc_checkarray = []
    for i in range(int(samples/10)):
      #for a in bytearr:
        #print(a)
      bytearr = ser.read(65)
      #crc = Crc16.calc(bytearr[:-3])

      #print("packet ",i,": ",f"{bytearr[0]} {bytearr[1]} {bytearr[2]} {bytearr[3]} {bytearr[4]} {bytearr[5]} {bytearr[6]} {bytearr[7]} {bytearr[8]} {bytearr[9]}")
      print(i," packet ",bytes_to_16bitint(bytearr[60],bytearr[61]),": ",*bytearr)
      if i ==bytes_to_16bitint(bytearr[60],bytearr[61]):
          packetcheckarray.append(True)
      else:
          packetcheckarray.append(False)

      if crc16(bytearr,length=63)==bytes_to_16bitint(bytearr[63],bytearr[64]):
          serial_crc_checkarray.append(True)
      else:
          serial_crc_checkarray.append(False)

      if bytearr[62]==1:
          spi_crc_checkarray.append(True)
      else:
          spi_crc_checkarray.append(False)
      print("python crc: ",crc16(bytearr,length=63))
      print("arduin crc: ",bytes_to_16bitint(bytearr[63],bytearr[64]))
      print("spi_error_flag: ",bytearr[62])

      for j in range(10):
        test = bytes_to_24bitint(bytearr[(j * 6):(j * 6) + 3])
        powerarray_ch0.append((test / 6990506.667)+0.0003)  # shunt
        powerarray_ch1.append(bytes_to_24bitint(bytearr[(j * 6)+3:(j * 6)+6]) / 6990506.667)  # core
    print("received packets: (should be 200) ",len(packetcheckarray))

    clockregistervalues=ser.read(2)
    print("Registerwert binär ID: (should be: 0b100010 0b101) ",bin(clockregistervalues[0]),bin(clockregistervalues[1]))
    clockregistervalues=ser.read(2)
    print("Registerwert binär Status: ",bin(clockregistervalues[0]),bin(clockregistervalues[1]))
    clockregistervalues=ser.read(2)
    print("Registerwert binär Mode: (should be: 0b101 0b10000) ",bin(clockregistervalues[0]),bin(clockregistervalues[1]))
    clockregistervalues=ser.read(2)
    print("Registerwert binär clock: (should be (64khz): 0b11 0b100010) ",bin(clockregistervalues[0]),bin(clockregistervalues[1]))

    temperaturevalues = ser.read(6)
    intambi = bytes_to_16bitint(temperaturevalues[0],temperaturevalues[1])
    intpack = bytes_to_16bitint(temperaturevalues[2],temperaturevalues[3])
    intambi*= 0.02;
    intpack*= 0.02;
    intambi-= 273.15;
    intpack-= 273.15;
    if crc16(temperaturevalues, length=4) == bytes_to_16bitint(temperaturevalues[4], temperaturevalues[5]):
        serial_crc_checkarray.append(True)
    else:
        serial_crc_checkarray.append(False)
    print("ambient-Temp: ","{:.2f}".format(intambi)," °C")
    print("package-Temp: ","{:.2f}".format(intpack)," °C")

    for i,j in enumerate(packetcheckarray):
        if j ==False:
            print("..packages lost at package: ",i)
            print("packetcheckarray: ",packetcheckarray)
    for i,j in enumerate(serial_crc_checkarray):
        if j ==False:
            print("..serial crc incorrect at package: ",i)
            print("chksumarray: ",serial_crc_checkarray)
    for i,j in enumerate(spi_crc_checkarray):
        if j ==True:
            print("..spi crc incorrect at package: ",i)
            print("spi_crc_checkarray: ",spi_crc_checkarray)

    print("----------Start Error Message summary-----------")
    if False in packetcheckarray:
        print("Packages lost!! ")
    if False in serial_crc_checkarray:
        print("Serial crc incorrect!! ")
    if True in spi_crc_checkarray:
        print("Spi crc incorrect!! ")
    print("----------End Error Message summary-----------")
    return(powerarray_ch0,powerarray_ch1,intambi,intpack)#,chip_temperature,ambient_temperature)

if __name__=='__main__':
  # parse arguments
  parser = argparse.ArgumentParser(description='This is a script to automatically do measurements on the PYNQ board with the power measurement circuit board')
  parser.add_argument('-d','--directories',help='colon-separated list of directories that contains bitstream files relative to /home/bitstreams; e.g. "test1:test2" if your bitstream files are located in /home/bitstreams/test1 and /home/bitstreams/test2')
  parser.add_argument('-s','--samples',help='number of consecutive measurements per bitstream file (useful to detect temperature dependencies)')
  parser.add_argument('-p', '--plot', help='0 or 1, show png of data, dont forget -Y in Terminal. Default= 0')
  parser.add_argument('-m', '--machine', help='executing machine; can be "sopwith" or "kangaroo". Default="kangaroo"')
  
  # execute vivado in this folder
  execute_folder = '/home/delft/vivado-exec/'
  
  # read user inputs
  parser_args = parser.parse_args()
  sub_dirs_str = parser_args.directories
  if sub_dirs_str == None:
    raise Exception('Must provide directory for measurement - call script with -h for help')
  sub_dirs = sub_dirs_str.split(':')
  num_points = 1
  try:
    num_points = int(parser_args.samples)
  except:
    print(f'Error while parsing arguments: failed to convert {parser_args.samples} to an integer, using {num_points} measurement points as a default value')
  plotting= 0
  try:
    plotting = int(parser_args.plot)
    if plotting < 0 or plotting > 1:
      raise Exception(f"Invalid value for --plot detected: expected 0 or 1 but got {plotting}")
  except:
    print(f'Error while parsing arguments: failed to convert {parser_args.plot} to an integer -> plotting disabled')
  machine = parser_args.machine
  if machine == None:
    machine = "sopwith"
  if not (machine == "sopwith" or machine == "kangaroo"):
    raise Exception(f"unknown machine '{machine}'; only sopwith and kangaroo are supported at the moment")
  
  # set machine-specific stuff
  if machine == "kangaroo":
    # pynq board ID
    pynq_measure = '*/xilinx_tcf/Digilent/003017AA4ED6A'
    # some parameters for power calculation
    shunt_r = 0.025185882
    gain_factor = 13.195
    offset = 0.002099464
    # address of remote-controlled power outlet
    system_code = "11111"
    unit_code = "10000"
    # device id of the arduino to communicate via usb serial protocol
    arduino_usb_device_id = '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'
  else: # sopwith
    # pynq board ID
    pynq_measure = '*/xilinx_tcf/Digilent/003017A6DD49A'
    # some parameters for power calculation
    shunt_r = 0.05965
    gain_factor = 7.0976
    offset = 0.0 # ToDo: determine pls
    # address of remote-controlled power outlet
    system_code = "11111"
    unit_code = "10101"
    arduino_usb_device_id = '/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0'
  
  # safety feature denying multiple runs at the same time
  multiple_access_deny_folder = '/home/delft/python-scripts/power-measurement/access-deny-folder'
  if not (os.path.exists(multiple_access_deny_folder)):
    os.mkdir(multiple_access_deny_folder)
  multiple_access_deny_file = f'/home/delft/python-scripts/power-measurement/access-deny-folder/{machine}_script_already_running.txt'
  if os.path.exists(multiple_access_deny_file):
    raise Exception(f'Another instance of this script is already running. You can start another measurement run when the folder /home/delft/python-scripts/power-measurement/access-deny-folder does not contain the file "{machine}_script_already_running.txt" anymore.')
  else:
    with open (multiple_access_deny_file , "w") as f:
      f.write("ongoing measurement run, please wait until this file is deleted when this run ends, thanks :)")
  # path to temporary tcl script file that we are using to control vivado
  tcl_script_path = '/home/delft/tcl-scripts/temp-vivado.tcl'
  
  try:  
    # let's go
    start(system_code, unit_code)
    time.sleep(1)
    print('started lab - performing measurements now...')

    
    bitstream_dir = '/home/delft/bitstreams'
    for sub_dir in sub_dirs:
      try:
        os.mkdir('/home/delft/results/' + sub_dir)
        print('/home/delft/results/' + sub_dir ,  " Created ")
      except FileExistsError:
        print('/home/delft/results/' + sub_dir ,  " already exists")
      print('starting measurements for all bitstreams in subdirectory '+sub_dir)
      with open('/home/delft/results/'+sub_dir+'/'+sub_dir+'.csv','w') as f:
        f.write('bitstream;num_points;static_power;dynamic_power;total_power;object_temperature;ambient_temperature\n')
        for filename in os.listdir(bitstream_dir+'/'+sub_dir):
          # skip non-bitstream files
          if not filename.endswith(".bit"): 
            print(f'  skipping {filename} because it is no bitstream')
            continue
          print(f'  doing measurements for bitstream "{filename}"')

          bitstream_filename = bitstream_dir + '/' + sub_dir + '/' + filename
          program(bitstream_filename, hw_target=pynq_measure)
          print('    programmed FPGA')

          # pull down reset for RNG

          powerarray_ch0, powerarray_ch1,intambi,intpack = measure_serial_bytes("/dev/cu.usbserial-02586B21", 0.025, 1,0)  # /dev/cu.usbserial-02586B21 sopwith 02588068

          voltagearray_combined = []
          for j in range(200):
            voltagearray_combined.append(powerarray_ch0[j])
            voltagearray_combined.append(powerarray_ch1[j])

          powerarray_combined = []
          for j in voltagearray_combined:
            powerarray_combined.append(j * 1.02 / (shunt_r * gain_factor))
          for i,j in enumerate(powerarray_combined):
            f.write('{};{};{};{};{};{};{}\n'.format(filename,400,0,0,powerarray_combined[i],intpack,intambi))
            f.flush()

          plt.figure(figsize=(28, 7))
          plt.plot(np.arange(400) , powerarray_combined , color="darkred",#32000
              label="Power_t_run1", alpha=0.8)
          plt.show()
          plt.savefig('/home/delft/results/'+sub_dir + '/' + sub_dir+"_"+filename[:-4]+".png")
          plt.close()
          print('    finished measurement for bitstream '+filename)
          print('    waiting a minute for the FPGA to cool down again...')
          for i in range(60):
            if i<=50:
              print(f'    ..{60-i}')
            else:
              print(f'    ...{60-i}')
            time.sleep(1)
        f.close()    
    close(system_code, unit_code)
    print('finished measurements and shut down lab')
    if os.path.exists(multiple_access_deny_file):
      os.remove(multiple_access_deny_file)
  except Exception as e:
    print(f'Detected measurement failure: "{e}" - cleaning up the mess, now...')
    close(system_code, unit_code)
    if os.path.exists(multiple_access_deny_file):
      os.remove(multiple_access_deny_file)
      
      
      
      
