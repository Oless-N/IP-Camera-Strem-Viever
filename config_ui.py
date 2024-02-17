from PySide6 import QtWidgets


class CameraAddDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Camera")
        self.layout = QtWidgets.QVBoxLayout()
        self.login_field = QtWidgets.QLineEdit()
        self.password_field = QtWidgets.QLineEdit()
        self.host_field = QtWidgets.QLineEdit()
        self.port_field = QtWidgets.QLineEdit()
        self.page_field = QtWidgets.QLineEdit()
        self.add_button = QtWidgets.QPushButton("Add")

        self.layout.addWidget(QtWidgets.QLabel("Login:"))
        self.layout.addWidget(self.login_field)
        self.layout.addWidget(QtWidgets.QLabel("Password:"))
        self.layout.addWidget(self.password_field)
        self.layout.addWidget(QtWidgets.QLabel("Host:"))
        self.layout.addWidget(self.host_field)
        self.layout.addWidget(QtWidgets.QLabel("Port:"))
        self.layout.addWidget(self.port_field)
        self.layout.addWidget(QtWidgets.QLabel("Page:"))
        self.layout.addWidget(self.page_field)
        self.layout.addWidget(self.add_button)

        self.setLayout(self.layout)

        self.add_button.clicked.connect(self.accept)

    def get_camera_info(self):
        return {
            "login": self.login_field.text(),
            "password": self.password_field.text(),
            "host": self.host_field.text(),
            "port": self.port_field.text(),
            "page": self.page_field.text(),
        }
