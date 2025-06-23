import serial
import serial.tools.list_ports
import logging
import threading

from .select_serial_view import SelectSerialView

_logger = logging.getLogger(__name__)


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


class DummyPort():
    def write(*args, **kwargs):
        pass


class DiscoboxController():

    def __init__(self, no_con=False):
        self.port = None
        self.port_open = False
        
        if no_con:
            return

        ports = serial.tools.list_ports.comports()
        ports = [
            port for port in ports
            if port.manufacturer and (port.manufacturer.find('Arduino')
                                      or port.manufacturer.find('arduino'))]
        
        if len(ports) == 0:
            return
        elif len(ports) == 1:
            self.select_serial(ports[0].device)
        else:
            SelectSerialView(self.select_serial, ports).start()
    
    def select_serial(self, device=None):
        if device is None:
            return
        
        self.port = serial.Serial(port=device, baudrate=9600)

    def start(self):
        if not self.port:
            return
        
        self.s = self.port.__enter__()
        self.port_open = True
        self.thread = threading.Thread(target=self.read_port, args=(self.port,), daemon=True)
        self.thread.start()
    
    def stop(self):
        if not self.port:
            return

        self.port_open = False
        self.thread.join()
        self.port.__exit__()
        self.s = None

    def read_port(self, port: serial.Serial):
        while self.port_open:
            data = port.read(1)
            # _logger.info(f'serial read: {data}')
        
    def __enter__(self, *args, **kwargs):
        if self.port is None:
            return DummyPort()
        return self.s
    
    def __exit__(self, *args, **kwargs):
        if self.port is None:
            return
        self.s.flush()

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
