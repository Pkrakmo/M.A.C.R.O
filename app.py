from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QRadioButton, QButtonGroup, QLineEdit, QHBoxLayout, QGroupBox, QTextBrowser, QTabWidget
from PySide6.QtCore import Qt, QThread, Signal, QRect
from PySide6.QtGui import QIcon  # Add this import
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key
import keyboard
import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "clicker_settings.json")

class ClickerThread(QThread):
    click_signal = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.running = False
        self.frequency = 100
        
    def run(self):
        while self.running:
            self.click_signal.emit()
            self.msleep(self.frequency)

    def stop(self):
        self.running = False
        self.wait()

class MITLicenseWidget(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        license_file = os.path.join(os.path.dirname(__file__), "TheMITLicense.html")
        with open(license_file, "r", encoding="utf-8") as file:
            self.setHtml(file.read())
        self.setOpenExternalLinks(True)

class SoftwareLicenseWidget(QTextBrowser):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)
        license_file = os.path.join(os.path.dirname(__file__), "Software.html")
        with open(license_file, "r", encoding="utf-8") as file:
            self.setHtml(file.read())
        self.setOpenExternalLinks(True)

class LicenseWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("License and Software Information")
        self.setGeometry(100, 100, 600, 400)
        
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()
        
        self.macro_license_widget = MITLicenseWidget()
        self.tab_widget.addTab(self.macro_license_widget, "The MIT License")

        self.software_license_widget = SoftwareLicenseWidget()
        self.tab_widget.addTab(self.software_license_widget, "Software information")
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

class KeyClickerHolder(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("M.A.C.R.O.")
        self.setFixedSize(297, 336)
        self.setWindowIcon(QIcon("icon.png"))  # Set the window icon
        
        # Center the window on the screen
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
        
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.selected_key = None
        self.device_used = "mouse"
        
        self.clicker_thread = ClickerThread()
        self.clicker_thread.click_signal.connect(self.perform_click)
        
        self.init_ui()
        self.load_settings()
        keyboard.add_hotkey("F6", self.toggle_clicking)
        
        self.license_window = None  # Initialize license_window as None
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Device selection
        self.device_group_box = QGroupBox("Device")
        device_layout = QHBoxLayout()
        self.device_group = QButtonGroup()
        self.mouse_radio = QRadioButton("Mouse")
        self.keyboard_radio = QRadioButton("Keyboard")
        self.device_group.addButton(self.mouse_radio)
        self.device_group.addButton(self.keyboard_radio)
        device_layout.addWidget(self.mouse_radio)
        device_layout.addWidget(self.keyboard_radio)
        self.device_group_box.setLayout(device_layout)
        layout.addWidget(self.device_group_box)
        
        # Action selection
        self.action_group_box = QGroupBox("Action")
        action_layout = QHBoxLayout()
        self.action_group = QButtonGroup()
        self.auto_click = QRadioButton("Autoclick")
        self.hold_click = QRadioButton("Hold")
        self.auto_click.setChecked(True)
        self.action_group.addButton(self.auto_click)
        self.action_group.addButton(self.hold_click)
        action_layout.addWidget(self.auto_click)
        action_layout.addWidget(self.hold_click)
        self.action_group_box.setLayout(action_layout)
        layout.addWidget(self.action_group_box)
        
        # Mouse buttons (Only visible if Mouse is selected)
        self.mouse_group_box = QGroupBox("Mouse Button")
        mouse_button_layout = QHBoxLayout()
        self.mouse_button_group = QButtonGroup()
        self.left_click = QRadioButton("Left Click")
        self.middle_click = QRadioButton("Middle Click")
        self.right_click = QRadioButton("Right Click")
        self.mouse_button_group.addButton(self.left_click)
        self.mouse_button_group.addButton(self.middle_click)
        self.mouse_button_group.addButton(self.right_click)
        self.left_click.setChecked(True)
        mouse_button_layout.addWidget(self.left_click)
        mouse_button_layout.addWidget(self.middle_click)
        mouse_button_layout.addWidget(self.right_click)
        self.mouse_group_box.setLayout(mouse_button_layout)
        layout.addWidget(self.mouse_group_box)
        
        # Keyboard key selection (Only visible if Keyboard is selected)
        self.keyboard_group_box = QGroupBox("Keyboard Key")
        keyboard_layout = QHBoxLayout()
        self.key_label = QLabel("No key selected")
        self.key_label.setAlignment(Qt.AlignCenter)
        keyboard_layout.addWidget(self.key_label)
        self.keyboard_group_box.setLayout(keyboard_layout)
        layout.addWidget(self.keyboard_group_box)
        
        self.key_label.mousePressEvent = self.set_key
        
        # Frequency input
        self.freq_label = QLabel("Autoclick frequency (ms):")
        layout.addWidget(self.freq_label)
        self.freq_input = QLineEdit("100")
        layout.addWidget(self.freq_input)
        
        # Start/Stop button
        self.start_stop_btn = QPushButton("Start (F6)")
        self.start_stop_btn.clicked.connect(self.toggle_clicking)
        layout.addWidget(self.start_stop_btn)
        
        # License label with hyperlink
        self.license_label = QLabel('<a href="#">License and Software Information</a>')
        self.license_label.setOpenExternalLinks(False)
        self.license_label.linkActivated.connect(self.show_license)
        layout.addWidget(self.license_label)
        
        self.setLayout(layout)
        
        # Connect device selection to visibility changes
        self.mouse_radio.toggled.connect(self.update_ui_visibility)
        self.keyboard_radio.toggled.connect(self.update_ui_visibility)
    
    def show_license(self):
        if self.license_window is None:
            self.license_window = LicenseWindow()
            self.license_window.setParent(self, Qt.Window)
        # Set the position of the LicenseWindow to be the same as the main window
        self.license_window.move(self.x(), self.y())
        self.license_window.show()
    
    def update_ui_visibility(self):
        is_mouse_selected = self.mouse_radio.isChecked()
        self.mouse_group_box.setVisible(is_mouse_selected)
        self.keyboard_group_box.setVisible(not is_mouse_selected)
        self.action_group_box.setVisible(is_mouse_selected)
        self.device_used = "mouse" if is_mouse_selected else "keyboard"
    
    def toggle_clicking(self):
        if self.clicker_thread.isRunning():
            self.clicker_thread.stop()
            self.start_stop_btn.setText("Start (F6)")
        else:
            self.clicker_thread.frequency = int(self.freq_input.text())
            self.clicker_thread.running = True
            self.clicker_thread.start()
            self.start_stop_btn.setText("Stop (F6)")
        self.save_settings()
    
    def perform_click(self):
        if self.mouse_radio.isChecked():
            button = Button.left if self.left_click.isChecked() else Button.middle if self.middle_click.isChecked() else Button.right
            self.mouse.click(button)
        elif self.keyboard_radio.isChecked() and self.selected_key:
            self.keyboard.press(self.selected_key)
            self.keyboard.release(self.selected_key)
    
    def set_key(self, event):
        self.key_label.setText("Press any key...")
        def on_press(key):
            self.selected_key = key.char if hasattr(key, 'char') else str(key)
            self.key_label.setText(str(self.selected_key))
            self.save_settings()
            listener.stop()
        from pynput.keyboard import Listener
        listener = Listener(on_press=on_press)
        listener.start()
    
    def save_settings(self):
        settings = {
            "selected_key": self.selected_key if self.selected_key else None,
            "frequency": self.freq_input.text(),
            "device_used": self.device_used,
            "left": self.left_click.isChecked(),
            "middle": self.middle_click.isChecked(),
            "right": self.right_click.isChecked(),
        }
        with open(SETTINGS_FILE, "w") as file:
            json.dump(settings, file)
    
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as file:
                settings = json.load(file)
                self.selected_key = settings.get("selected_key")
                if self.selected_key:
                    self.key_label.setText(self.selected_key)
                self.freq_input.setText(settings.get("frequency", "100"))
                self.mouse_radio.setChecked(settings.get("device_used", "mouse") == "mouse")
                self.keyboard_radio.setChecked(settings.get("device_used", "mouse") == "keyboard")
                self.left_click.setChecked(settings.get("left", True))
                self.middle_click.setChecked(settings.get("middle", False))
                self.right_click.setChecked(settings.get("right", False))
                self.update_ui_visibility()

if __name__ == "__main__":
    app = QApplication([])
    window = KeyClickerHolder()
    window.show()
    try:
        app.exec()
    except KeyboardInterrupt:
        print("Application interrupted by user. Exiting...")