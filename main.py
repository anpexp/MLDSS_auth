import sys
import requests
import base64
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QPushButton, QTabWidget, QMessageBox
)

API_URL = "http://127.0.0.1:5000"  # Dirección de la API Flask

class RegistrationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # Formulario para el nombre de usuario durante el registro.
        formLayout = QFormLayout()
        self.username_input = QLineEdit()
        formLayout.addRow("Nombre de Usuario:", self.username_input)
        layout.addLayout(formLayout)

        self.btn_generate_keys = QPushButton("Generar Claves")
        self.btn_generate_keys.clicked.connect(self.generate_keys)
        layout.addWidget(self.btn_generate_keys)

        self.public_key_label = QLabel("Clave Pública: [No generada]")
        self.private_key_label = QLabel("Clave Privada: [Guardada en dispositivo]")
        layout.addWidget(self.public_key_label)
        layout.addWidget(self.private_key_label)

        self.setLayout(layout)

    def generate_keys(self):
        username = self.username_input.text()
        if not username:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de usuario.")
            return
        
        response = requests.post(f"{API_URL}/register", json={"username": username})
        if response.status_code == 201:
            data = response.json()
            self.public_key = data["public_key"]
            self.private_key = data["secret_key"]

            self.public_key_label.setText(f"Clave Pública: {self.public_key[:20]}...")
            self.private_key_label.setText(f"Clave Privada: {self.private_key[:20]}... (Guardada localmente)")

            QMessageBox.information(self, "Éxito", f"Usuario '{username}' registrado.")
        else:
            QMessageBox.warning(self, "Error", response.json().get("error", "Error desconocido."))

class LoginTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        formLayout = QFormLayout()
        self.username_login = QLineEdit()
        formLayout.addRow("Nombre de Usuario:", self.username_login)
        layout.addLayout(formLayout)

        self.btn_generate_challenge = QPushButton("Generar Desafío")
        self.btn_generate_challenge.clicked.connect(self.generate_challenge)
        layout.addWidget(self.btn_generate_challenge)

        self.challenge_label = QLabel("Desafío: [No generado]")
        layout.addWidget(self.challenge_label)

        self.btn_sign_challenge = QPushButton("Firmar Desafío")
        self.btn_sign_challenge.clicked.connect(self.sign_challenge)
        layout.addWidget(self.btn_sign_challenge)

        self.verification_label = QLabel("Estado: [Pendiente]")
        layout.addWidget(self.verification_label)

        self.setLayout(layout)
        self.challenge = None
        self.private_key = None

    def generate_challenge(self):
        username = self.username_login.text()
        if not username:
            QMessageBox.warning(self, "Error", "Ingrese un nombre de usuario.")
            return
        
        response = requests.get(f"{API_URL}/challenge", params={"username": username})
        if response.status_code == 200:
            data = response.json()
            self.challenge = data["challenge"]
            self.challenge_label.setText(f"Desafío: {self.challenge[:20]}...")
            QMessageBox.information(self, "Éxito", "Desafío generado.")
        else:
            QMessageBox.warning(self, "Error", response.json().get("error", "Error desconocido."))

    def sign_challenge(self):
        username = self.username_login.text()
        if not username or not self.challenge:
            QMessageBox.warning(self, "Error", "Debe generar un desafío primero.")
            return
        
        # Se asume que el usuario ya generó su clave privada en el registro
        self.private_key = requests.post(f"{API_URL}/register", json={"username": username}).json().get("secret_key")
        if not self.private_key:
            QMessageBox.warning(self, "Error", "No se encontró la clave privada del usuario.")
            return

        response = requests.post(f"{API_URL}/sign", json={
            "username": username,
            "message": self.challenge
        })

        if response.status_code == 200:
            signature = response.json()["signature"]
            verify_response = requests.post(f"{API_URL}/login", json={
                "username": username,
                "signature": signature
            })

            if verify_response.status_code == 200:
                self.verification_label.setText("Estado: Autenticado")
                QMessageBox.information(self, "Éxito", "Firma válida. Acceso concedido.")
            else:
                self.verification_label.setText("Estado: Fallido")
                QMessageBox.warning(self, "Error", "Firma inválida.")
        else:
            QMessageBox.warning(self, "Error", "No se pudo firmar el desafío.")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Login con MLDSS")
        self.setGeometry(100, 100, 600, 400)

        self.tabs = QTabWidget()
        self.registration_tab = RegistrationTab()
        self.login_tab = LoginTab()

        self.tabs.addTab(self.registration_tab, "Registro")
        self.tabs.addTab(self.login_tab, "Login")

        self.setCentralWidget(self.tabs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
