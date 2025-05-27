import serial

SOM = b'\x53'

byte_to_cmd_dict = {
    b'\x60': 'Poll',
    b'\x61': 'ID Report Request',
    b'\x62': 'Peripheral Device Capabilities Request',
    b'\x64': 'Local Status Report Request',
    b'\x65': 'Input Status Report Request',
    b'\x66': 'Output Status Report Request',
    b'\x67': 'Reader Status Tamper Report Request',
    b'\x68': 'Output Control Command',
    b'\x69': 'Reader LED Control Command',
    b'\x6A': 'Reader Buzzer Control Command',
    b'\x6B': 'Reader Text Output Command',
    b'\x6E': 'Communication Configuration Command',
    b'\x73': 'Scan and Send Biometric Data',
    b'\x74': 'Scan and Match Biometric Data',
    b'\x75': 'Encryption Key Set',
    b'\x76': 'Challenge and Secure Session Initialization Request',
    b'\x77': 'Server’s Random Number and Server Cryptogram',
    b'\x7B': 'Maximum Acceptable Reply Size',
    b'\x7C': 'File Transfer Command',
    b'\x80': 'Manufacturer Specific Command',
    b'\xA1': 'Extended Write Data',
    b'\xA2': 'Abort PD Operation',
    b'\xA3': 'Get PIV Data',
    b'\xA4': 'Request Authenticate',
    b'\xA5': 'Request Crypto Response',
    b'\xA7': 'Keep Secure Channel Active'
}


byte_to_reply_dict = {
    b'\x40': 'General Acknowledge, Nothing to Report',
    b'\x41': 'Negative Acknowledge – SIO Comm Handler Error Response',
    b'\x45': 'Device Identification Report',
    b'\x46': 'Device Capabilities Report',
    b'\x48': 'Local Status Report',
    b'\x49': 'Input Status Report',
    b'\x4A': 'Output Status Report',
    b'\x4B': 'Reader Status Tamper Report',
    b'\x50': 'Card Data Report, Raw Bit Array',
    b'\x51': 'Card Data Report, Character Array',
    b'\x53': 'Keypad Data Report',
    b'\x54': 'Communication Configuration Report',
    b'\x57': 'Biometric Data',
    b'\x58': 'Biometric Match Result',
    b'\x76': 'Client’s ID and Client’s Random Number',
    b'\x78': 'Client Cryptogram Packet and the Initial R-MAC',
    b'\x79': 'PD Is Busy Reply',
    b'\x7A': 'File Transfer Status',
    b'\x80': 'PIV Data Reply',
    b'\x81': 'Authentication Response',
    b'\x82': 'Response to Challenge',
    b'\x83': 'Manufacturer Specific Status',
    b'\x84': 'Manufacturer Specific Error',
    b'\x90': 'Manufacturer Specific Reply',
    b'\xB1': 'Extended Read Response'
}


byte_to_cmd_unique_dict = {
    key: value for key, value in byte_to_cmd_dict.items() if key not in byte_to_reply_dict
}

byte_to_reply_unique_dict = {
    key: value for key, value in byte_to_reply_dict.items() if key not in byte_to_cmd_dict
}

def wait_for_som(serial_line):
        header = serial_line.read(1)
        return header == SOM

class DeviceClass:
    def __init__(self):
        self.address = ""
        self.address_byte = b'\x00'
        self.is_control_panel = False
        self.is_peripheral_device = False

    def set_address(self, address_byte):
        self.address = address_byte.hex()
        self.address_byte = address_byte

    def set_type_control_panel(self):
        self.is_control_panel = True
        self.is_peripheral_device = False

    def set_type_peripheral_device(self):
        self.is_control_panel = False
        self.is_peripheral_device = True

class FrameHandlerClass:
    def __init__(self, serial_line):
        self.serial_line = serial_line
    def get_frame(self):
        got_SOM = False
        bytes_read = 0
        while not got_SOM:
            got_SOM = wait_for_som(self.serial_line)
        #print("Got SOM!")
        frame_handler_frame = FrameClass()
        frame_handler_frame.address_byte = self.serial_line.read(1)
        frame_handler_frame.length_bytes = self.serial_line.read(2)
        frame_handler_frame.length = int.from_bytes(frame_handler_frame.length_bytes, byteorder='little')
        if frame_handler_frame.length > 65535: raise Exception("Frame length invalid: Greater than theoretical maximum.") 
        frame_handler_frame.control_byte = self.serial_line.read(1)
        bytes_read = 5
        # Masking to check what is in use:
        frame_handler_frame.SCB = (bytes([frame_handler_frame.control_byte[0] & bytes(b'\x08')[0]])[0]) == bytes(b'\x08')[0]
        frame_handler_frame.SQN = (bytes([frame_handler_frame.control_byte[0] & bytes(b'\x03')[0]]))
        frame_handler_frame.CRC = (bytes([frame_handler_frame.control_byte[0] & bytes(b'\x04')[0]])[0]) == bytes(b'\x04')[0]
        #Handle SCB (Security Control Block) ((Always plaintext :3))
        if frame_handler_frame.SCB:
            frame_handler_frame.scb_blk_len_byte = self.serial_line.read(1)
            frame_handler_frame.scb_blk_type_byte = self.serial_line.read(1)
            bytes_read += 2
            if int.from_bytes(frame_handler_frame.scb_blk_len_byte, byteorder='little') <= 3:
                frame_handler_frame.scb_blk_data_bytes = self.serial_line.read(int.from_bytes(frame_handler_frame.scb_blk_len_byte, byteorder='little') - 2) 
                bytes_read += int.from_bytes(frame_handler_frame.scb_blk_len_byte, byteorder='little') - 2

        frame_handler_frame.command_byte = self.serial_line.read(1)

        #Calculate and get length for message data!
        if frame_handler_frame.CRC:
             bytesToRead = (frame_handler_frame.length - bytes_read) - 3
        else:
             bytesToRead = (frame_handler_frame.length - bytes_read) - 2

        frame_handler_frame.data_bytes = self.serial_line.read(bytesToRead)

        if frame_handler_frame.CRC:
            frame_handler_frame.CRC_bytes = self.serial_line.read(2)
        else:
            frame_handler_frame.checksum_byte = self.serial_line.read(1)
        self.serial_line.reset_input_buffer()
        frame_handler_frame.printFrameHex()
        return frame_handler_frame


        
class FrameClass:
    def __init__(self):
        ## CTRL Meta
        self.CRC = False
        self.SQN = -1
        self.SCB = False
        ##Header
        self.address_byte = b'\x00'
        self.length_bytes = b'\x00\x00'
        self.length = int(0)
        #Message control Information
        self.control_byte = b'\x00'

        #SCB
        self.scb_blk_len_byte = b'\x00'
        self.scb_blk_type_byte = b'\x00'
        self.scb_blk_data_bytes = b'\x00'

        #Command/Reply data
        self.command_byte = b'\x00'
        self.data_bytes = b'\x00'

        # MAC (Only present in secure messages)
        self.MAC_bytes = b'\x00\x00\x00\x00'

        #Packet Validation
        self.checksum_byte = b'\x00'

        self.CRC_bytes = b'\x00\x00'

    def printFrameHex(self):
                ## CTRL Meta

        ##Header
        print("Addr: " + self.address_byte.hex())
        print("Len (LSB,MSB): " + self.length_bytes.hex())
        print("Converted length: " + str(self.length))
        print("Ctrl: ", self.control_byte.hex())
        print("Sequence #: ", self.SQN)
        print("Using CRC?: ", self.CRC)
        print("SCB Included?", self.SCB)

        #SCB
        if self.SCB:
            print("SCB Block length: " + self.scb_blk_len_byte.hex())
            print("SCB Block type: " + self.scb_blk_type_byte.hex())
            print("SCB Block data: " + self.scb_blk_data_bytes.hex())

        #Command/Reply data
        print("Command/Reply: " + self.command_byte.hex())

        print("Data: " + self.data_bytes.hex())

        # MAC (Only present in secure messages)

        #Packet Validation
        if not self.CRC:
            print("Checksum: " + self.checksum_byte.hex())
        else:
            print("CRC: " + self.CRC_bytes.hex())
        print("")


    def printFrameHexMessage(self):
        message = []
        ## CTRL Meta

        ##Header
        message.append("Addr: " + self.address_byte.hex())
        message.append("Len (LSB,MSB): " + self.length_bytes.hex())
        message.append("Converted length: " + str(self.length))
        message.append("Ctrl: ", self.control_byte.hex())
        message.append("Sequence #: ", self.SQN)
        message.append("Using CRC?: ", self.CRC)
        message.append("SCB Included?", self.SCB)

        #SCB
        if self.SCB:
            message.append("SCB Block length: " + self.scb_blk_len_byte.hex())
            message.append("SCB Block type: " + self.scb_blk_type_byte.hex())
            message.append("SCB Block data: " + self.scb_blk_data_bytes.hex())

        #Command/Reply data
        message.append("Command/Reply: " + self.command_byte.hex())
        message.append("Data: " + self.data_bytes.hex())

        # MAC (Only present in secure messages)

        #Packet Validation
        if not self.CRC:
            message.append("Checksum: " + self.checksum_byte.hex())
        else:
            message.append("CRC: " + self.CRC_bytes.hex())
            
        return message
    