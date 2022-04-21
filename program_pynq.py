import os
import argparse

def create_tcl_script(tcl_script_path, bitstream_path, hw_server, hw_target, hw_comm_frequency, hw_device):
  with open(tcl_script_path,'w') as f:
    f.write('open_hw_manager\n')
    f.write('connect_hw_server -url {} -allow_non_jtag\n'.format(hw_server))
    f.write('current_hw_target [get_hw_targets {}]\n'.format(hw_target))
    f.write('set_property PARAM.FREQUENCY {} [get_hw_targets {}]\n'.format(hw_comm_frequency,hw_target))
    f.write('open_hw_target\n')
    f.write('set_property PROGRAM.FILE {{{}}} [get_hw_devices {}]\n'.format(bitstream_path,hw_device))
    f.write('current_hw_device [get_hw_devices {}]\n'.format(hw_device))
    f.write('refresh_hw_device -update_hw_probes false [lindex [get_hw_devices {}] 0]\n'.format(hw_device))
    f.write('set_property PROBES.FILE {{}} [get_hw_devices {}]\n'.format(hw_device))
    f.write('set_property FULL_PROBES.FILE {{}} [get_hw_devices {}]\n'.format(hw_device))
    f.write('set_property PROGRAM.FILE {{{}}} [get_hw_devices {}]\n'.format(bitstream_path,hw_device))
    f.write('program_hw_devices [get_hw_devices {}]\n'.format(hw_device))
    f.write('refresh_hw_device [lindex [get_hw_devices {}] 0]\n'.format(hw_device))
  return

def start_vivado(vivado_binary,tcl_script_path):
  os.system('{} -nolog -nojournal -notrace -mode batch -source {} -quiet'.format(vivado_binary, tcl_script_path))
  return

def program(bitstream_path, hw_server=None, hw_target=None, hw_comm_frequency=None, hw_device=None, vivado_binary=None):
  # default values
  if hw_server==None:
    hw_server = 'localhost:3121'
  if hw_target==None:
    hw_target = '*/xilinx_tcf/Digilent/003017AA4ED6A'
  if hw_comm_frequency==None:
    hw_comm_frequency = '15000000'
  if hw_device==None:
    hw_device = 'xc7z020_1'
  if vivado_binary==None:
    vivado_binary = '/opt/xilinx/vitis2020.2/Vivado/2020.2/bin/vivado'
  
  if bitstream_path==None:
    raise Exception('Need to specify bitstream path!')
  
  # path to temporary tcl script file that we are using to control vivado
  tcl_script_path = '/home/delft/tcl-scripts/temp-vivado.tcl'
  
  create_tcl_script(tcl_script_path, bitstream_path, hw_server, hw_target, hw_comm_frequency, hw_device)
  start_vivado(vivado_binary,tcl_script_path)
  return

if __name__ == '__main__':
  # create argument parser
  parser = argparse.ArgumentParser(description='This is a script that loads a bit file on an fpga using vivado; example call: "python program-pynq.py -b /home/dtprakt0/bitstreams/tasterXor.bit -s localhost:3121 -t */xilinx_tcf/Digilent/003017AA4F82A -c 15000000 -d xc7z020_1 -v /opt/xilinx/vitis2020.2/Vivado/2020.2/bin/vivado"')
  parser.add_argument('-b','--bitstream_path',help='path to bitstream file that you want to load on the FPGA, e.g. /home/username/asdf.bit')
  parser.add_argument('-s','--hw_server',help='OPTIONAL - hardware server, default: localhost:3121')
  parser.add_argument('-t','--hw_target',help='OPTIONAL - hardware target that you want to program, default: */xilinx_tcf/Digilent/003017AA4F82A')
  parser.add_argument('-c','--hw_comm_frequency',help='OPTIONAL - hardware target communication frequency, default: 15000000 for PYNQ boards')
  parser.add_argument('-d','--hw_device',help='OPTIONAL - hardware device that you want to program, default: xc7z020_1')
  parser.add_argument('-v','--vivado_binary',help='OPTIONAL - path to vivado binary, default: /opt/xilinx/vitis2020.2/Vivado/2020.2/bin/vivado')
  
  # read user inputs
  parser_args = parser.parse_args()
  bitstream_path = parser_args.bitstream_path
  hw_server = parser_args.hw_server
  hw_target = parser_args.hw_target
  hw_comm_frequency = parser_args.hw_comm_frequency
  hw_device = parser_args.hw_device
  vivado_binary = parser_args.vivado_binary
  
  program(bitstream_path, hw_server, hw_target, hw_comm_frequency, hw_device, vivado_binary)
