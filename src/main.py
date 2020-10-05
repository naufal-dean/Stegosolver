import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
from ui.gui import MainWindow
from controller import StegoAudio, StegoImage, StegoImageBPCS, StegoVideo


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
