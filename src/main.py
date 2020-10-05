import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
from ui.gui import MainWindow
from controller import StegoAudio, StegoImage, StegoImageBPCS, StegoVideo
from controller.audio_controller import psnr

# if __name__ == '__main__':
#     ic = StegoImage('example/raw.png')
#     ic.insert_data('main.py', False, 'someseed')
#     ic.image.save('test.png')
#     oc = StegoImage('test.png')
#     f = oc.extract_data('test.txt', 'someseed')
#     print(f)
#     exit()
# if __name__ == '__main__':
#     key = "STEGANO"
#     path = "example/test.wav"
#     hide = StegoAudio(key, path)
#     hide.insert_data("example/test.pdf", 1)
#     hide.save_stego_audio("example/save.wav")
#     extractor = StegoAudio(key, "example/save.wav")
#     extractor.extract_data()
#     extractor.save_extracted_file("example/cok.pdf")
#     psnr("example/test.wav", "example/save.wav")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec())
