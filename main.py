from PyQt5 import QtWidgets
from app import HEXARApp

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    window = HEXARApp()
    window.ui.show()
    app.exec()