# -*- coding: utf-8 -*-
"""RS485 communication module."""

import serial


class RS485Communication:
    """
    Handles RS485 communication.
    Note: For many USB-to-RS485 converters, the software implementation
    is identical to UART. Hardware handles direction control. If manual
    RTS/DTR toggling is needed, this class would need expansion.
    """

    def __init__(self, port, baudrate, timeout=1):
        """
        Initializes the RS485 communication object.

        Args:
            port (str): The serial port name (e.g., '/dev/ttyUSB0').
            baudrate (int): The communication speed.
            timeout (int): Read timeout in seconds.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_conn = None

    def connect(self):
        """Establishes the serial connection for RS485."""
        if self.serial_conn and self.serial_conn.is_open:
            return
        try:
            # For RS485, often same settings as UART work directly.
            # More advanced setups might need rtscts=True or specific GPIO control.
            self.serial_conn = serial.Serial(
                self.port, self.baudrate, timeout=self.timeout
            )
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open RS485 port {self.port}: {e}")

    def disconnect(self):
        """Closes the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.serial_conn = None

    def is_connected(self):
        """Checks if the serial port is open."""
        return self.serial_conn and self.serial_conn.is_open

    def send_data(self, data):
        """
        Sends data over RS485.

        Args:
            data (str): The string data to send.

        Raises:
            ConnectionError: If not connected.
        """
        if not self.is_connected():
            raise ConnectionError("RS485 not connected.")
        try:
            # Before sending, one might toggle a GPIO pin for the transceiver's DE pin
            self.serial_conn.write(data.encode('utf-8'))
            # After sending, wait for transmission to complete then toggle DE pin off
            self.serial_conn.flush()
        except serial.SerialTimeoutException as e:
            raise TimeoutError(f"RS485 send timeout: {e}")

    def receive_data(self):
        """
        Receives data from RS485.

        Returns:
            str: The received data, decoded as UTF-8.

        Raises:
            ConnectionError: If not connected.
        """
        if not self.is_connected():
            raise ConnectionError("RS485 not connected.")
        
        # Before receiving, one might ensure the transceiver's RE pin is enabled
        received_data = self.serial_conn.readline()
        return received_data.decode('utf-8', errors='ignore').strip()
