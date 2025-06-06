import serial
import time


COMMANDS = {
    'vent': 0x00,
    'led1': 0x01,
    'led2': 0x02,
    'led1_on_off': 0x03,
    'led2_on_off': 0x04,
    'led_on_off': 0x05,
    'vent_on_off': 0x06,
    'all_off': 0x07,
}


class DiscoboxController():

    def __init__(self):
        self.port = serial.Serial(
            port='/dev/ttyACM0', baudrate=9600)
        
    def __enter__(self, *args, **kwargs):
        return self.port.__enter__(*args, **kwargs)
    
    def __exit__(self, *args, **kwargs):
        self.port.__exit__(*args, **kwargs)

    def set_vent(self, val: int):
        return self._get_packet(
            COMMANDS['vent'],
            val)

    def set_led1(self, val: int):
        return self._get_packet(
            COMMANDS['led1'],
            val)

    def set_led2(self, val: int):
        return self._get_packet(
            COMMANDS['led2'],
            val)

    def set_led1_on(self, on: bool = True):
        return self._get_packet(
            COMMANDS['led1_on_off'],
            0x01 if on else 0x00)

    def set_led2_on(self, on: bool = True):
        return self._get_packet(
            COMMANDS['led2_on_off'],
            0x01 if on else 0x00)

    def set_led_on(self, on: bool = True):
        return self._get_packet(
            COMMANDS['led_on_off'],
            0x01 if on else 0x00)

    def set_vent_on(self, on: bool = True):
        return self._get_packet(
            COMMANDS['vent_on_off'],
            0x01 if on else 0x00)

    def set_all_off(self):
        return self._get_packet(
            COMMANDS['all_off'],
            0x00)

    def _get_packet(self, cmd, val):
        packet = bytearray()
        packet.append(cmd)
        packet.append(val)
        packet.append(cmd ^ val)
        return packet
