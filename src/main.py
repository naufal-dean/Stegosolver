import sys
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QFile


if __name__ == '__main__':
    # Create app
    app = QtWidgets.QApplication(sys.argv)
    # Create window
    window = QtWidgets.QMainWindow()
    # Load layout ui
    uifile = QFile("ui/main.ui")
    uifile.open(QFile.ReadOnly)
    uic.loadUi(uifile, window)
    uifile.close()
    # Show window
    window.show()
    # Exec app
    app.exec_()
