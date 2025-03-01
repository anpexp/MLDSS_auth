import sys
import random
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QLabel, QMessageBox, QTabWidget, QTextEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# Importaciones para Matplotlib integrado en PyQt5
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation

##########################################
# Parámetros y funciones básicas MLDSS   #
##########################################

q = 23      # Módulo (número primo pequeño, solo para ejemplificar)
dim = 2     # Dimensión de los vectores y matrices

def random_vector(dim, low=-2, high=2):
    return [random.randint(low, high) for _ in range(dim)]

def random_matrix(dim, low=0, high=10):
    return [[random.randint(low, high) for _ in range(dim)] for _ in range(dim)]

def mat_vec_mult(matrix, vector, mod):
    result = []
    for row in matrix:
        val = sum(x * y for x, y in zip(row, vector)) % mod
        result.append(val)
    return result

def simple_hash(m, mod):
    return sum(ord(c) for c in m) % mod

def sign(m, A, s, q):
    # Paso 1: Generar vector aleatorio r
    r = random_vector(dim, -2, 2)
    # Paso 2: Calcular u = A * r mod q
    u = mat_vec_mult(A, r, q)
    # Paso 3: Calcular el reto c combinando u y el hash simple del mensaje
    c = (sum(u) + simple_hash(m, q)) % q
    # Paso 4: Calcular la firma σ = r + c * s mod q (suma componente a componente)
    sigma = [(r_i + c * s_i) % q for r_i, s_i in zip(r, s)]
    return sigma, c

def verify(m, sigma, c, A, pk, q):
    # Paso 1: Calcular A * σ mod q
    Asigma = mat_vec_mult(A, sigma, q)
    # Paso 2: Calcular c * pk
    cp = [(c * pk_i) % q for pk_i in pk]
    # Paso 3: Obtener u' = A * σ - c * pk mod q
    u_prime = [((a - b) % q) for a, b in zip(Asigma, cp)]
    # Paso 4: Recalcular c' y comparar
    c_prime = (sum(u_prime) + simple_hash(m, q)) % q
    return c_prime == c, u_prime, c_prime

# Generar un parámetro público A global (simula la retícula común)
A = random_matrix(dim, 0, 10)

# "Base de datos" simulada para usuarios: username -> (password, clave privada s, clave pública pk)
registered_users = {}

##########################################
# Pestaña de Registro                    #
##########################################

class RegistrationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.register_button = QPushButton("Registrar")
        self.register_button.clicked.connect(self.register_user)
        
        layout.addRow("Nombre de usuario:", self.username_input)
        layout.addRow("Contraseña:", self.password_input)
        layout.addRow("", self.register_button)
        
        self.setLayout(layout)
    
    def register_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Complete todos los campos.")
            return
        if username in registered_users:
            QMessageBox.warning(self, "Error", "El usuario ya existe.")
            return
        # Generar clave privada (s) y calcular la clave pública (pk = A * s mod q)
        s = random_vector(dim, -2, 2)
        pk = mat_vec_mult(A, s, q)
        registered_users[username] = (password, s, pk)
        QMessageBox.information(
            self, "Registro exitoso",
            f"Usuario '{username}' registrado.\nClave pública: {pk}"
        )
        self.username_input.clear()
        self.password_input.clear()

##########################################
# Pestaña de Login                       #
##########################################

class LoginTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Iniciar Sesión")
        self.login_button.clicked.connect(self.login_user)
        
        layout.addRow("Nombre de usuario:", self.username_input)
        layout.addRow("Contraseña:", self.password_input)
        layout.addRow("", self.login_button)
        
        self.setLayout(layout)
    
    def login_user(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            QMessageBox.warning(self, "Error", "Complete todos los campos.")
            return
        if username not in registered_users:
            QMessageBox.warning(self, "Error", "Usuario no registrado.")
            return
        stored_password, s, pk = registered_users[username]
        if password != stored_password:
            QMessageBox.warning(self, "Error", "Contraseña incorrecta.")
            return
        
        # Simular proceso de login mediante MLDSS (firmar un reto)
        mensaje_login = "login challenge"
        signature, challenge = sign(mensaje_login, A, s, q)
        is_valid, _, _ = verify(mensaje_login, signature, challenge, A, pk, q)
        
        if is_valid:
            QMessageBox.information(self, "Acceso concedido", "Autenticación exitosa.")
            self.open_protected_window(s)
        else:
            QMessageBox.warning(self, "Acceso denegado", "Firma digital no válida.")
    
    def open_protected_window(self, secret):
        self.protected_window = ProtectedWindow(secret)
        self.protected_window.show()
        self.username_input.clear()
        self.password_input.clear()

##########################################
# Ventana con Contenido Protegido        #
##########################################

class ProtectedWindow(QMainWindow):
    def __init__(self, secret):
        super().__init__()
        self.secret = secret  # vector secreto del usuario autenticado
        self.setWindowTitle("Contenido Protegido")
        self.setGeometry(200, 200, 600, 500)
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        title = QLabel("Bienvenido al sistema seguro")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        content = QTextEdit()
        content.setReadOnly(True)
        content.setText(
            "Este es el contenido protegido del sistema.\n\n"
            "Aquí podrías mostrar información sensible o recursos exclusivos."
        )
        
        # Botón para mostrar el diagrama estático del proceso MLDSS
        self.diagram_button = QPushButton("Mostrar Diagrama del Proceso")
        self.diagram_button.clicked.connect(self.show_diagram)
        
        # Botón para simular un ataque de fuerza bruta con animación
        self.bruteforce_button = QPushButton("Simular Ataque de Fuerza Bruta")
        self.bruteforce_button.clicked.connect(self.show_bruteforce_animation)
        
        layout.addWidget(title)
        layout.addWidget(content)
        layout.addWidget(self.diagram_button)
        layout.addWidget(self.bruteforce_button)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
    
    def show_diagram(self):
        self.diagram_window = ProcessGraphWindow()
        self.diagram_window.show()
    
    def show_bruteforce_animation(self):
        # Se pasa el vector secreto del usuario (s) para simular el ataque
        self.bruteforce_window = BruteForceAnimationWindow(A, self.secret, q, low=-2, high=2)
        self.bruteforce_window.show()

##########################################
# Ventana para el Diagrama estático con Matplotlib
##########################################

class ProcessGraphWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagrama del Proceso MLDSS")
        self.setGeometry(300, 300, 800, 600)
        self.init_ui()
    
    def init_ui(self):
        self.figure = Figure(figsize=(8,6))
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.draw_diagram()
    
    def draw_diagram(self):
        ax = self.figure.add_subplot(111)
        ax.clear()
        ax.axis('off')
        
        # Definir las posiciones y textos de los nodos (x, y, descripción)
        nodes = {
            "s": (0.1, 0.8, "Clave privada s"),
            "A": (0.1, 0.6, "Parámetro público A"),
            "pk": (0.1, 0.4, "Clave pública pk = A * s mod q"),
            "r": (0.45, 0.8, "Generar vector r"),
            "u": (0.45, 0.6, "Calcular u = A * r mod q"),
            "c": (0.45, 0.4, "Calcular reto c = f(u, m)"),
            "sigma": (0.45, 0.2, "Calcular firma σ = r + c * s mod q"),
            "Asigma": (0.8, 0.8, "Calcular A * σ mod q"),
            "c_pk": (0.8, 0.6, "Calcular c * pk"),
            "u_prime": (0.8, 0.4, "Obtener u' = A * σ - c * pk mod q"),
            "c_prime": (0.8, 0.2, "Recalcular c' = f(u', m)"),
            "verify": (0.8, 0.1, "Verificar: c' == c")
        }
        
        # Dibujar los nodos como cajas de texto
        for key, (x, y, text) in nodes.items():
            ax.text(x, y, text, ha='center', va='center', fontsize=10,
                    bbox=dict(facecolor='lightblue', edgecolor='black', boxstyle='round,pad=0.5'))
        
        # Dibujar las flechas que unen los nodos
        self.draw_arrow(ax, nodes["s"], nodes["sigma"])
        self.draw_arrow(ax, nodes["A"], nodes["u"])
        self.draw_arrow(ax, nodes["r"], nodes["u"])
        self.draw_arrow(ax, nodes["u"], nodes["c"])
        self.draw_arrow(ax, nodes["c"], nodes["sigma"])
        self.draw_arrow(ax, nodes["sigma"], nodes["Asigma"])
        self.draw_arrow(ax, nodes["pk"], nodes["c_pk"])
        self.draw_arrow(ax, nodes["c"], nodes["c_prime"])
        self.draw_arrow(ax, nodes["Asigma"], nodes["u_prime"])
        self.draw_arrow(ax, nodes["c_pk"], nodes["u_prime"])
        self.draw_arrow(ax, nodes["u_prime"], nodes["c_prime"])
        self.draw_arrow(ax, nodes["c_prime"], nodes["verify"])
        
        self.canvas.draw()
    
    def draw_arrow(self, ax, start, end):
        start_x, start_y, _ = start
        end_x, end_y, _ = end
        ax.annotate("",
                    xy=(end_x, end_y + 0.05),
                    xytext=(start_x, start_y - 0.05),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color='gray'))

##########################################
# Ventana para la animación del Ataque de Fuerza Bruta
##########################################

class BruteForceAnimationWindow(QMainWindow):
    def __init__(self, A, secret, q, low=-2, high=2):
        super().__init__()
        self.setWindowTitle("Ataque de Fuerza Bruta")
        self.setGeometry(250, 250, 600, 600)
        self.A = A
        self.secret = secret
        self.q = q
        self.low = low
        self.high = high
        # Calcular la clave pública a partir del vector secreto
        self.pk = mat_vec_mult(self.A, self.secret, self.q)
        
        # Generar candidatos en el rango dado
        self.candidates = []
        for i in range(low, high+1):
            for j in range(low, high+1):
                self.candidates.append([i, j])
        
        # Determinar el candidato correcto según la ecuación: A * s_candidate mod q == pk
        self.correct_candidate = None
        for candidate in self.candidates:
            if mat_vec_mult(self.A, candidate, self.q) == self.pk:
                self.correct_candidate = candidate
                break
        
        # Configuración de la figura de Matplotlib
        self.figure = Figure(figsize=(6,6))
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlim(low-1, high+1)
        self.ax.set_ylim(low-1, high+1)
        self.ax.set_xlabel("Componente 1")
        self.ax.set_ylabel("Componente 2")
        self.ax.set_title("Ataque de Fuerza Bruta: Búsqueda del vector secreto")
        
        # Iniciar la animación: se actualiza cada 500 ms para mostrar el siguiente candidato
        self.animation = FuncAnimation(self.figure, self.update_plot, frames=len(self.candidates), interval=500, repeat=False)
    
    def update_plot(self, frame):
        self.ax.clear()
        self.ax.set_xlim(self.low-1, self.high+1)
        self.ax.set_ylim(self.low-1, self.high+1)
        self.ax.set_xlabel("Componente 1")
        self.ax.set_ylabel("Componente 2")
        self.ax.set_title("Ataque de Fuerza Bruta: Búsqueda del vector secreto")
        
        # Candidato actual que se está evaluando
        candidate = self.candidates[frame]
        # Dibujar el vector candidato como una flecha desde el origen
        self.ax.quiver(0, 0, candidate[0], candidate[1], angles='xy', scale_units='xy', scale=1, color='red')
        self.ax.text(candidate[0], candidate[1], f"{candidate}", color='black')
        
        # Si el candidato es el correcto, se resalta en verde
        if candidate == self.correct_candidate:
            self.ax.quiver(0, 0, candidate[0], candidate[1], angles='xy', scale_units='xy', scale=1, color='green', width=0.005)
            self.ax.text(candidate[0], candidate[1], f"{candidate} (Correcto)", color='green')
        
        # Mostrar en gris los candidatos evaluados previamente
        for i in range(frame):
            prev = self.candidates[i]
            self.ax.plot(prev[0], prev[1], 'o', color='gray', markersize=5)
        
        self.canvas.draw()

##########################################
# Ventana Principal con Pestañas         #
##########################################

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Login con MLDSS")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        tabs = QTabWidget()
        tabs.addTab(RegistrationTab(), "Registro")
        tabs.addTab(LoginTab(), "Login")
        self.setCentralWidget(tabs)
        
        # Estilos para un aspecto profesional
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QLineEdit, QPushButton {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #2E86C1;
                color: white;
            }
            QPushButton:hover {
                background-color: #1B4F72;
            }
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 4px;
                margin: 0px;
            }
            QTabBar::tab {
                background: #eee;
                padding: 10px;
                border: 1px solid #ccc;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background: white;
                font-weight: bold;
            }
        """)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())
