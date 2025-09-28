# -*- coding: utf-8 -*-
"""CAN communication module."""

import can


class CANCommunication:
    """Handles CAN communication using python-can."""

    def __init__(self, channel, bitrate=500000, interface='socketcan'):
        """
        Initializes the CAN communication object.

        Args:
            channel (str): CAN interface channel (e.g., 'can0').
            bitrate (int): The bus speed in bits/sec.
            interface (str): The backend interface to use (e.g., 'socketcan').
        """
        self.channel = channel
        self.bitrate = bitrate
        self.interface = interface
        self.bus = None

    def connect(self):
        """Initializes the CAN bus."""
        if self.bus:
            return  # Already connected
        try:
            # Ensure the CAN interface is up before connecting
            # e.g., sudo ip link set can0 up type can bitrate 500000
            self.bus = can.Bus(
                interface=self.interface,
                channel=self.channel,
                bitrate=self.bitrate
            )
        except Exception as e:
            raise ConnectionError(f"Failed to initialize CAN bus on {self.channel}: {e}")

    def disconnect(self):
        """Shuts down the CAN bus."""
        if self.bus:
            self.bus.shutdown()
            self.bus = None

    def is_connected(self):
        """Checks if the CAN bus is initialized."""
        return self.bus is not None

    def send_data(self, data, arbitration_id=0x123):
        """
        Sends a message over the CAN bus.

        Args:
            data (str): String data to be encoded and sent.
            arbitration_id (int): The CAN message identifier.
        """
        if not self.is_connected():
            raise ConnectionError("CAN bus not connected.")
        try:
            message = can.Message(
                arbitration_id=arbitration_id,
                data=data.encode('utf-8'),
                is_extended_id=False
            )
            self.bus.send(message)
        except can.CanError as e:
            raise IOError(f"Error sending CAN message: {e}")

    def receive_data(self, timeout=1.0):
        """
        Receives a message from the CAN bus.

        Args:
            timeout (float): Time to wait for a message in seconds.

        Returns:
            str: The decoded message data or None if timeout occurs.
        """
        if not self.is_connected():
            raise ConnectionError("CAN bus not connected.")
            
        message = self.bus.recv(timeout)
        if message:
            return message.data.decode('utf-8', errors='ignore')
        return None
