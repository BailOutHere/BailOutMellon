import blessed
import argparse
import serial
import osdp_handling
from threading import Thread
from time import sleep

term = blessed.Terminal()

parser = argparse.ArgumentParser(prog = 'attack', description = "Attack OSDP")
parser.add_argument("device", type = str, metavar = "PATH", help = "Path to serial device")
parser.add_argument("--baudrate", type = int, metavar = "N", default = 115200, help = "Serial port's baud rate (default: 115200)")
parser.add_argument('-1', '--sniff',
                    action='store_true')
parser.add_argument('-2', '--downgrade',
                    action='store_true')
parser.add_argument('-3', '--install',
                    action='store_true')
parser.add_argument('-4', '--weakkey',
                    action='store_true')
args = parser.parse_args()


class InformationTrackerClass:
    def __init__(self, args, dataline):
        self.args = args
        self.frame = osdp_handling.FrameClass()
        self.frame_handler = osdp_handling.FrameHandlerClass(dataline)
        self.past_frames = []
        self.known_devices = []


    def update_known_devices(self):
        for frame in self.past_frames:
            if (len(self.known_devices) == 0) or all(frame.address_byte not in dev.address_byte for dev in self.known_devices):
                self.__if_control_panel_frame_append(frame)
                self.__if_peripheral_device_frame_append(frame)
                


    def __if_control_panel_frame_append(self, frame):
        if frame.command_byte in osdp_handling.byte_to_cmd_unique_dict:
            print("Found control panel!")
            new_control_panel = osdp_handling.DeviceClass()
            new_control_panel.set_address(frame.address_byte)
            new_control_panel.set_type_control_panel()
            self.known_devices.append(new_control_panel)
        

    def __if_peripheral_device_frame_append(self, frame):
        if frame.command_byte in osdp_handling.byte_to_reply_unique_dict:
            print("Found PD!")
            new_peripheral_device = osdp_handling.DeviceClass()
            new_peripheral_device.set_address(frame.address_byte)
            new_peripheral_device.set_type_peripheral_device()
            self.known_devices.append(new_peripheral_device)


    def update_all_information(self):
        self.update_known_devices()
    
'''
    def update_seen_uniq_commands(self):
        for cp in self.control_panels:
            for frame in self.past_frames:
                self.is_command_uniq(frame, cp)
'''

def setup():
    if not (args.downgrade or args.install or args.weakkey):
        args.sniff = True
    
    serial_line = serial.Serial(
            port=args.device,
            baudrate=args.baudrate,
            timeout=0.1,
        )
    
    tracked_information = InformationTrackerClass(args, serial_line)

    serial_thread = Thread(target=serial_loop, args=(tracked_information,))
    serial_thread.start()

    information_tracker_thread = Thread(target=update_information_loop, args=(tracked_information,))
    information_tracker_thread.start()

    terminal_loop(tracked_information)


def serial_loop(tracked_information):
    while True:
        frame = tracked_information.frame_handler.get_frame()
        #print("Got Frame!")
        if len(tracked_information.past_frames) >= 100: tracked_information.past_frames.pop(0)
        tracked_information.past_frames.append(frame)



def update_information_loop(tracked_information):
    while True:
        update_devices_thread = Thread(target=tracked_information.update_all_information(), args=())
        update_devices_thread.start()
        

def terminal_loop(tracked_information):
    while True:
        '''
        print(term.home + term.clear)
        print(tracked_information.known_devices)
        print("Known CPs:")
        for dev in tracked_information.known_devices:
            if dev.is_control_panel:
                print("    Address: ", dev.address)
        print("")
        print("Known PDs:")
        for dev in tracked_information.known_devices:
            if dev.is_peripheral_device:
                print("    Address: ", dev.address)
        '''
        sleep(5)


setup()