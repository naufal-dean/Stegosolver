import sys
from PyQt5 import uic
from PyQt5 import QtWidgets
from PyQt5.QtCore import QFile

from controller import StegoImage


if __name__ == '__main__':
    ic = StegoImage('example/raw.png')
    ic.insert_data('main.py', False, 'someseed')
    ic.image.save('test.png')
    oc = StegoImage('test.png')
    f = oc.extract_data('test.txt', 'someseed')
    print(f)
    exit()

if __name__ == '__main__':
    # Create app
    app = QtWidgets.QApplication(sys.argv)
    # Create window
    window = QtWidgets.QMainWindow()
    # Load layout ui
    uifile = QFile('ui/main.ui')
    uifile.open(QFile.ReadOnly)
    uic.loadUi(uifile, window)
    uifile.close()
    # Show window
    window.show()
    # Exec app
    app.exec_()
