import argparse
import serial

parser = argparse.ArgumentParser(prog = 'attack', description = "Read UART Data")
parser.add_argument("device", type = str, metavar = "PATH", help = "Path to serial device")
parser.add_argument("--baudrate", type = int, metavar = "N", default = 115200, help = "Serial port's baud rate (default: 115200)")
args = parser.parse_args()


serial_line = serial.Serial(
        port=args.device,
        baudrate=args.baudrate,
        timeout=0.1,
    )

while True:
    bytes = serial_line.read(16)
    if bytes != b"":
        print(bytes.hex())
