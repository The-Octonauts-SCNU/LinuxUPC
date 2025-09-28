# -*- coding: utf-8 -*-
"""I2C communication module."""

import smbus


class I2CCommunication:
    """Handles I2C communication using smbus."""

    def __init__(self, bus_number, device_address):
        """
        Initializes the I2C communication object.

        Args:
            bus_number (int): The I2C bus number (e.g., 1 for Raspberry Pi).
            device_address (int): The I2C address of the slave device.
        """
        self.bus_number = bus_number
        self.device_address = device_address
        self.bus = None
        self._connected = False

    def connect(self):
        """Initializes the SMBus."""
        if self.bus:
            return  # Already connected
        try:
            self.bus = smbus.SMBus(self.bus_number)
            # A simple read to check if device is present
            self.bus.read_byte(self.device_address)
            self._connected = True
        except (FileNotFoundError, IOError) as e:
            self._connected = False
            raise ConnectionError(
                f"Failed to open I2C bus {self.bus_number} or "
                f"find device at address {hex(self.device_address)}: {e}"
            )

    def disconnect(self):
        """Closes the SMBus connection."""
        if self.bus:
            self.bus.close()
            self.bus = None
        self._connected = False

    def is_connected(self):
        """Checks if the connection is active."""
        return self._connected

    def send_data(self, data, register=None):
        """
        Sends data over I2C. Can send a list of bytes or a string.

        Args:
            data (str or list[int]): Data to send. If string, it's converted
                                     to a list of ASCII values.
            register (int, optional): The register to write to. If None,
                                      writes a block of data.
        """
        if not self.is_connected():
            raise ConnectionError("I2C not connected.")

        if isinstance(data, str):
            data_bytes = [ord(c) for c in data]
        elif isinstance(data, list):
            data_bytes = data
        else:
            raise TypeError("Data must be a string or a list of integers.")

        try:
            if register is not None:
                # Write a block of data to a specific register
                self.bus.write_i2c_block_data(
                    self.device_address, register, data_bytes
                )
            else:
                # Simple write, sends the first byte of data
                if data_bytes:
                    self.bus.write_byte(self.device_address, data_bytes[0])
        except IOError as e:
            raise IOError(f"I2C write failed: {e}")

    def receive_data(self, num_bytes=1, register=None):
        """
        Receives data from I2C.

        Args:
            num_bytes (int): Number of bytes to read.
            register (int, optional): The register to read from.

        Returns:
            list[int]: A list of bytes read from the device.
        """
        if not self.is_connected():
            raise ConnectionError("I2C not connected.")
        
        try:
            if register is not None:
                return self.bus.read_i2c_block_data(
                    self.device_address, register, num_bytes
                )
            else:
                return [self.bus.read_byte(self.device_address) for _ in range(num_bytes)]
        except IOError as e:
            raise IOError(f"I2C read failed: {e}")
