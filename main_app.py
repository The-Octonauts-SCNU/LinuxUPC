# -*- coding: utf-8 -*-
"""
Host Computer Assistant Main Application
Author: BaleDeng
Date: 2025-09-20
"""
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit,
                             QComboBox, QGroupBox, QTextEdit, QTabWidget,
                             QGridLayout, QMessageBox)
from PyQt5.QtCore import QThread, pyqtSignal, QObject
from PyQt5.QtGui import QIcon, QFont

# Import communication modules
from communication.uart_comm import UARTCommunication
from communication.rs485_comm import RS485Communication
from communication.can_comm import CANCommunication
from communication.i2c_comm import I2CCommunication

# --- Global Stylesheet ---
STYLE_SHEET = """
QWidget {
    background-color: #1E1E1E;
    color: #E0E0E0;
    font-family: 'Segoe UI';
    font-size: 14px;
}
QMainWindow {
    border: 1px solid #FF69B4;
}
QGroupBox {
    border: 1px solid #FF69B4;
    border-radius: 8px;
    margin-top: 10px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 10px;
    color: #FF69B4;
}
QLabel {
    color: #E0E0E0;
}
QLineEdit, QTextEdit, QComboBox {
    background-color: #2D2D2D;
    border: 1px solid #4A4A4A;
    border-radius: 5px;
    padding: 5px;
}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
    border: 1px solid #FF69B4;
}
QPushButton {
    background-color: #FF69B4;
    color: #1E1E1E;
    border: none;
    padding: 8px 16px;
    border-radius: 5px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #FF85C1;
}
QPushButton:pressed {
    background-color: #E05297;
}
QPushButton:disabled {
    background-color: #555555;
    color: #888888;
}
QTabWidget::pane {
    border: 1px solid #4A4A4A;
    border-radius: 5px;
}
QTabBar::tab {
    background: #2D2D2D;
    color: #E0E0E0;
    padding: 8px 20px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    border: 1px solid #4A4A4A;
    margin-right: 2px;
}
QTabBar::tab:selected {
    background: #FF69B4;
    color: #1E1E1E;
    font-weight: bold;
}
"""


class CommunicationWorker(QObject):
    """
    Worker thread for handling continuous data reception to prevent UI freezing.
    """
    data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    _is_running = True

    def __init__(self, comm_instance):
        super().__init__()
        self.comm = comm_instance

    def run(self):
        """Continuously listens for incoming data."""
        self._is_running = True
        while self._is_running:
            try:
                data = self.comm.receive_data()
                if data:
                    self.data_received.emit(str(data))
                QThread.msleep(50)  # Prevent high CPU usage
            except Exception as e:
                self.error_occurred.emit(f"Data reception error: {e}")
                break

    def stop(self):
        """Stops the listening loop."""
        self._is_running = False


class ParameterAdjustmentWindow(QWidget):
    """
    A separate window for adjusting other vehicle parameters.
    This serves as an extension point for future features.
    """
    send_param_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("高级参数调节 (Advanced Parameter Tuning)")
        self.setWindowIcon(QIcon.fromTheme("preferences-system"))
        self.setGeometry(200, 200, 400, 300)
        self.initUI()
        self.setStyleSheet(STYLE_SHEET)

    def initUI(self):
        layout = QGridLayout(self)
        layout.setSpacing(15)

        # Yaw
        layout.addWidget(QLabel("Yaw Angle:"), 0, 0)
        self.yaw_input = QLineEdit("0.0")
        layout.addWidget(self.yaw_input, 0, 1)

        # Roll
        layout.addWidget(QLabel("Roll Angle:"), 1, 0)
        self.roll_input = QLineEdit("0.0")
        layout.addWidget(self.roll_input, 1, 1)

        # Distance
        layout.addWidget(QLabel("Linear Distance:"), 2, 0)
        self.distance_input = QLineEdit("0.0")
        layout.addWidget(self.distance_input, 2, 1)

        send_button = QPushButton("发送参数 (Send Parameters)")
        send_button.clicked.connect(self.send_parameters)
        layout.addWidget(send_button, 3, 0, 1, 2)

    def send_parameters(self):
        """Formats and emits the parameter data."""
        yaw = self.yaw_input.text()
        roll = self.roll_input.text()
        dist = self.distance_input.text()
        # Example command format, can be customized
        command = f"PARAMS,{yaw},{roll},{dist}"
        self.send_param_signal.emit(command)
        QMessageBox.information(self, "Success", "参数已发送！ (Parameters sent!)")
        self.close()


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("上位机助手 (Host Computer Assistant)")
        self.setWindowIcon(QIcon.fromTheme("utilities-terminal"))
        self.setGeometry(100, 100, 800, 600)

        self.comm_instance = None
        self.worker_thread = None
        self.comm_worker = None
        self.param_window = None

        self.initUI()
        self.setStyleSheet(STYLE_SHEET)
        self.update_connection_inputs()

    def initUI(self):
        """Initializes the User Interface components."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # --- Left Panel: Connection and Log ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        main_layout.addWidget(left_panel, 1)

        # Connection Group
        conn_group = QGroupBox("通信设置 (Communication Settings)")
        conn_layout = QGridLayout(conn_group)
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["UART", "RS485", "CAN", "I2C"])
        conn_layout.addWidget(QLabel("协议 (Protocol):"), 0, 0)
        conn_layout.addWidget(self.protocol_combo, 0, 1)

        # Dynamic inputs based on protocol
        self.port_label = QLabel("端口 (Port):")
        self.port_input = QLineEdit("/dev/ttyUSB0")
        self.baud_label = QLabel("波特率 (Baudrate):")
        self.baud_input = QLineEdit("115200")
        self.channel_label = QLabel("通道 (Channel):")
        self.channel_input = QLineEdit("can0")
        self.bus_label = QLabel("总线 (Bus):")
        self.bus_input = QLineEdit("1")
        self.addr_label = QLabel("地址 (Address):")
        self.addr_input = QLineEdit("0x42")

        conn_layout.addWidget(self.port_label, 1, 0)
        conn_layout.addWidget(self.port_input, 1, 1)
        conn_layout.addWidget(self.baud_label, 2, 0)
        conn_layout.addWidget(self.baud_input, 2, 1)
        conn_layout.addWidget(self.channel_label, 3, 0)
        conn_layout.addWidget(self.channel_input, 3, 1)
        conn_layout.addWidget(self.bus_label, 4, 0)
        conn_layout.addWidget(self.bus_input, 4, 1)
        conn_layout.addWidget(self.addr_label, 5, 0)
        conn_layout.addWidget(self.addr_input, 5, 1)

        self.connect_button = QPushButton("连接 (Connect)")
        conn_layout.addWidget(self.connect_button, 6, 0, 1, 2)
        left_layout.addWidget(conn_group)

        # 日志组
        log_group = QGroupBox("日志 (Log)")
        log_layout = QVBoxLayout(log_group)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        left_layout.addWidget(log_group)

        # --- Right Panel: Control Tabs ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, 2)

        tabs = QTabWidget()
        pid_tab = QWidget()
        other_params_tab = QWidget()

        tabs.addTab(pid_tab, "PID 调节 (PID Tuning)")
        tabs.addTab(other_params_tab, "其他 (Others)")
        right_layout.addWidget(tabs)

        # PID 参数整定
        pid_group = QGroupBox("PID 参数 (PID Parameters)")
        pid_layout = QGridLayout(pid_group)
        pid_tab.setLayout(QVBoxLayout(pid_tab))
        pid_tab.layout().addWidget(pid_group)

        pid_layout.addWidget(QLabel("KP:"), 0, 0)
        self.kp_input = QLineEdit("1.0")
        pid_layout.addWidget(self.kp_input, 0, 1)
        pid_layout.addWidget(QLabel("KI:"), 1, 0)
        self.ki_input = QLineEdit("0.1")
        pid_layout.addWidget(self.ki_input, 1, 1)
        pid_layout.addWidget(QLabel("KD:"), 2, 0)
        self.kd_input = QLineEdit("0.01")
        pid_layout.addWidget(self.kd_input, 2, 1)

        self.send_pid_button = QPushButton("发送PID参数 (Send PID)")
        self.send_pid_button.setEnabled(False)
        pid_layout.addWidget(self.send_pid_button, 3, 0, 1, 2)

        # Other Parameters Tab
        other_params_layout = QVBoxLayout(other_params_tab)
        self.open_param_window_button = QPushButton("打开高级参数调节窗口")
        self.open_param_window_button.setStyleSheet(
            "background-color: #2D2D2D; border: 1px dashed #FF69B4;")
        self.open_param_window_button.setEnabled(False)
        other_params_layout.addWidget(self.open_param_window_button)
        other_params_layout.addStretch(1)

        # Connect signals
        self.connect_button.clicked.connect(self.toggle_connection)
        self.protocol_combo.currentTextChanged.connect(
            self.update_connection_inputs)
        self.send_pid_button.clicked.connect(self.send_pid_data)
        self.open_param_window_button.clicked.connect(self.open_param_window)

    def update_connection_inputs(self):
        """Shows/hides input fields based on selected protocol."""
        protocol = self.protocol_combo.currentText()
        is_serial = protocol in ["UART", "RS485"]
        is_can = protocol == "CAN"
        is_i2c = protocol == "I2C"

        self.port_label.setVisible(is_serial)
        self.port_input.setVisible(is_serial)
        self.baud_label.setVisible(is_serial)
        self.baud_input.setVisible(is_serial)

        self.channel_label.setVisible(is_can)
        self.channel_input.setVisible(is_can)
        # For CAN, baudrate can also be relevant (e.g., for socketcan)
        self.baud_label.setVisible(is_can)
        self.baud_input.setVisible(is_can)
        if is_can:
            self.baud_label.setText("比特率 (Bitrate):")
            self.baud_input.setText("500000")
        else:
            self.baud_label.setText("波特率 (Baudrate):")
            self.baud_input.setText("115200")

        self.bus_label.setVisible(is_i2c)
        self.bus_input.setVisible(is_i2c)
        self.addr_label.setVisible(is_i2c)
        self.addr_input.setVisible(is_i2c)

    def toggle_connection(self):
        """Connects or disconnects from the device."""
        if self.comm_instance and self.comm_instance.is_connected():
            self.disconnect_device()
        else:
            self.connect_device()

    def connect_device(self):
        """Establishes connection based on selected protocol."""
        protocol = self.protocol_combo.currentText()
        try:
            if protocol in ["UART", "RS485"]:
                port = self.port_input.text()
                baud = int(self.baud_input.text())
                self.comm_instance = UARTCommunication(
                    port, baud) if protocol == "UART" else RS485Communication(
                        port, baud)
            elif protocol == "CAN":
                channel = self.channel_input.text()
                bitrate = int(self.baud_input.text())
                self.comm_instance = CANCommunication(channel=channel,
                                                      bitrate=bitrate)
            elif protocol == "I2C":
                bus = int(self.bus_input.text())
                addr = int(self.addr_input.text(), 16)
                self.comm_instance = I2CCommunication(bus, addr)

            self.comm_instance.connect()
            self.log(f"[{protocol}] Connected successfully.")

            # Start worker thread for receiving data
            self.worker_thread = QThread()
            self.comm_worker = CommunicationWorker(self.comm_instance)
            self.comm_worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.comm_worker.run)
            self.comm_worker.data_received.connect(self.log)
            self.comm_worker.error_occurred.connect(self.handle_comm_error)

            self.worker_thread.start()

            # Update UI
            self.connect_button.setText("断开 (Disconnect)")
            self.protocol_combo.setEnabled(False)
            self.send_pid_button.setEnabled(True)
            self.open_param_window_button.setEnabled(True)

        except Exception as e:
            self.log(f"Error connecting: {e}")
            QMessageBox.critical(self, "Connection Error",
                                 f"Failed to connect: {e}")
            self.comm_instance = None

    def disconnect_device(self):
        """Closes the connection."""
        if self.comm_worker:
            self.comm_worker.stop()
        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()
        if self.comm_instance:
            self.comm_instance.disconnect()

        self.log("Disconnected.")
        self.comm_instance = None

        # 界面更新
        self.connect_button.setText("连接 (Connect)")
        self.protocol_combo.setEnabled(True)
        self.send_pid_button.setEnabled(False)
        self.open_param_window_button.setEnabled(False)

    # pid参数更新
    def send_pid_data(self):
        """Sends PID parameters to the device."""
        if not self.comm_instance or not self.comm_instance.is_connected():
            self.log("Not connected. Cannot send data.")
            return

        kp = self.kp_input.text()
        ki = self.ki_input.text()
        kd = self.kd_input.text()

        # Example command format: "PID,kp,ki,kd\n"
        # This should be adapted to the lower machine's protocol.
        command = f"PID,{kp},{ki},{kd}\n"

        try:
            self.comm_instance.send_data(command)
            self.log(f"Sent: {command.strip()}")
        except Exception as e:
            self.log(f"Error sending PID data: {e}")

    def send_custom_data(self, data):
        """Sends custom data from other windows."""
        if not self.comm_instance or not self.comm_instance.is_connected():
            self.log("Not connected. Cannot send data.")
            return

        command = f"{data}\n"
        try:
            self.comm_instance.send_data(command)
            self.log(f"Sent: {command.strip()}")
        except Exception as e:
            self.log(f"Error sending custom data: {e}")

    def open_param_window(self):
        """Opens the advanced parameter adjustment window."""
        if self.param_window is None:
            self.param_window = ParameterAdjustmentWindow()
            self.param_window.send_param_signal.connect(self.send_custom_data)
        self.param_window.show()

    def log(self, message):
        """Appends a message to the log display."""
        self.log_display.append(message)

    def handle_comm_error(self, error_message):
        """Handles communication errors from the worker."""
        self.log(f"ERROR: {error_message}")
        self.disconnect_device()
        QMessageBox.warning(self, "Communication Error", error_message)

    def closeEvent(self, event):
        """Ensures clean shutdown on window close."""
        self.disconnect_device()
        event.accept()


# 主函数入口

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
