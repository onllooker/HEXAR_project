import serial
import serial.tools.list_ports

class PortMonitor:
    def __init__(self) -> None:
        self.current_ports: set[str] = set()

    def get_current_ports(self) -> set[str]:
        available_ports = set()
        for port in serial.tools.list_ports.comports():
            try:
                with serial.Serial(port.device, timeout=1) as ser:
                    available_ports.add(port.device)
            except (OSError, serial.SerialException):
                # Порт занят или недоступен
                continue
        return available_ports

    def check_changes(self) -> tuple[list[str], list[str]]:
        new_ports = self.get_current_ports()
        added = new_ports - self.current_ports
        removed = self.current_ports - new_ports
        self.current_ports = new_ports
        return list(added), list(removed)

def baudrate() -> list[str]:
    return ['9600', '19200', '38400', '115200']
