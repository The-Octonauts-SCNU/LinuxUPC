# -*- coding: utf-8 -*-
"""UART (Serial) communication module."""

import serial


class UARTCommunication:
    """Handles UART communication using pyserial."""

    def __init__(self, port, baudrate, timeout=1):
        """
        Initializes the UART communication object.

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
        """Establishes the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            return  # Already connected
        try:
            self.serial_conn = serial.Serial(
                self.port, self.baudrate, timeout=self.timeout
            )
        except serial.SerialException as e:
            raise ConnectionError(f"Failed to open port {self.port}: {e}")

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
        Sends data over UART.

        Args:
            data (str): The string data to send.

        Raises:
            ConnectionError: If not connected.
        """
        if not self.is_connected():
            raise ConnectionError("UART not connected.")
        try:
            self.serial_conn.write(data.encode('utf-8'))
        except serial.SerialTimeoutException as e:
            raise TimeoutError(f"UART send timeout: {e}")

    def receive_data(self, num_bytes=None):
        """
        Receives data from UART. Reads one line by default.

        Args:
            num_bytes (int, optional): Number of bytes to read.
                                       If None, reads until a newline.

        Returns:
            str: The received data, decoded as UTF-8.

        Raises:
            ConnectionError: If not connected.
        """
        if not self.is_connected():
            raise ConnectionError("UART not connected.")
        if num_bytes:
            received_data = self.serial_conn.read(num_bytes)
        else:
            received_data = self.serial_conn.readline()
        
        return received_data.decode('utf-8', errors='ignore').strip()
