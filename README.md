## Bailoutmellon
Just a quick branch of the original mellon - mostly for my own learning an understanding. Added a control panel script and a pd script for simulating each, and my own attack scripts. Still under construction so there is a lot of missing functionality and it is MESSYYYY

### Usage
For this recipe you will need:

- Legit control panel | (cp_test.py & USB-RS485 converter)
- Legit peripheral devices(s) | (pd_test.py & USB-RS485 converter(s) per simulated device)
- bailattack.py, osdp_handling.py, and a USB-RS485 converter

Get it all wired up on a single bus (jumpers onto a bread board was my method), run cp_test.py and/or pd_test.py to simulate peripheral devices and/or control panels as needed, then you can run the script with ".\bailattack.py COM6 --baud 9600"

Note: At the moment all this does not have any fancy capabilities. It's still under construction. If you want something working, check out the original mellon!