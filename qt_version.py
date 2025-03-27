from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase
from PyQt5 import QtGui
from PyQt5.QtWidgets import *


from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command


from uuid import uuid1

from subprocess import call, Popen, STARTUPINFO, STARTF_USESHOWWINDOW, SW_HIDE
from sys import argv, exit, platform

import json
import os
import minecraft_launcher_lib
import random


minecraft_directory = get_minecraft_directory().replace('minecraft', 'vlaucnher')
settings_file = os.path.join(minecraft_directory, 'launcher_settings.json')

class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    version_id = ''
    username = ''

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username):
        self.version_id = version_id
        self.username = username
        
        if not os.path.exists(minecraft_directory):
            os.makedirs(minecraft_directory)
        with open(settings_file, 'w') as f:
            json.dump({'last_username': username}, f)
        
    
    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)
    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        

        self.state_update_signal.emit(True)

        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory, callback={ 'setStatus': self.update_progress_label, 'setProgress': self.update_progress, 'setMax': self.update_progress_max })

        if self.username == '':
            self.username = generate_username()[0]
            
        
        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        command = get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options)
        
        if platform == 'win32':
            startupinfo = STARTUPINFO()
            startupinfo.dwFlags |= STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = SW_HIDE
            Popen(command, startupinfo=startupinfo)
        else:
            call(command)
        self.state_update_signal.emit(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedSize(670, 640)
        self.centralwidget = QWidget(self)

        self.setWindowTitle('VanillaLauncher')
        self.setWindowIcon(QtGui.QIcon('assets/Window-logo.png'))

        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(512, 120))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap('assets/VLauncher-logo.png'))
        self.logo.setScaledContents(True)
        
        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Username')
        
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    if 'last_username' in settings:
                        self.username.setText(settings['last_username'])
            except:
                pass
        
        self.version_select = QComboBox(self.centralwidget)
        for version in get_version_list():
            self.version_select.addItem(version['id'])


        self.progress_spacer = QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 24)
        self.start_progress.setVisible(False)

        self.start_button_texture = QLabel(self.centralwidget)
        self.start_button_texture.setText('')
        self.start_button_texture.setFixedSize(310, 92)
        self.start_button_texture.setPixmap(QPixmap('assets/button.png'))
        self.start_button_texture.setScaledContents(True)
        self.start_button_texture.move(15, 535)
        
        minecraft_font_id = QFontDatabase.addApplicationFont('minecraft.ttf')
        minecraft_font = QFontDatabase.applicationFontFamilies(minecraft_font_id)[0]

        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Play')
        self.start_button.setFont(QFont(minecraft_font, 20))
        self.start_button.clicked.connect(self.launch_game)
        self.start_button.setFixedSize(310, 92)
        self.start_button.setStyleSheet('background-color: transparent; color: #2b2a2a;')
        
        self.vertical_layout = QVBoxLayout(self.centralwidget)
        self.vertical_layout.setContentsMargins(15, 15, 15, 15)
        self.vertical_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vertical_layout.addItem(self.titlespacer)
        self.vertical_layout.addWidget(self.username)
        self.vertical_layout.addWidget(self.version_select)
        self.vertical_layout.addItem(self.progress_spacer)
        self.vertical_layout.addWidget(self.start_progress_label)
        self.vertical_layout.addWidget(self.start_progress)
        self.vertical_layout.addWidget(self.start_button)

        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.setCentralWidget(self.centralwidget)
    
    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)
    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label) # Исправил проблему с созданием описания для полосы прогресса [24:01]
    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text())
        self.launch_thread.start()

if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    window = MainWindow()
    window.show()

    exit(app.exec_())
