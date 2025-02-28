from flask import Flask, request, jsonify
import oqs
import os
import base64

app = Flask(__name__)

# "Base de datos" en memoria para usuarios.
# Para cada usuario se almacena: public_key, secret_key (solo para demostración) y challenge temporal.
users = {}

def generate_keypair():
    """Genera un par de claves utilizando Dilithium2 (MLDSS basado en retículas modulares)."""
    with oqs.Signature("Dilithium2") as signer:
        public_key, secret_key = signer.generate_keypair()
    return public_key, secret_key

@app.route('/register', methods=['POST'])
def register():
    """
    Registro de usuario.
    Se recibe un JSON con el campo "username", se genera el par de claves y se almacena la clave pública.
    Para fines de demostración, se retorna también la clave privada (en un sistema real, ésta debe permanecer en el cliente).
    """
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"error": "El campo 'username' es obligatorio."}), 400
    if username in users:
        return jsonify({"error": "El usuario ya se encuentra registrado."}), 400

    public_key, secret_key = generate_keypair()
    # Convertir las claves a Base64 para facilitar su transporte en JSON
    public_key_b64 = base64.b64encode(public_key).decode('utf-8')
    secret_key_b64 = base64.b64encode(secret_key).decode('utf-8')
    users[username] = {"public_key": public_key, "secret_key": secret_key}
    
    return jsonify({
        "username": username,
        "public_key": public_key_b64,
        "secret_key": secret_key_b64  # En producción, la clave privada nunca se envía al cliente.
    }), 201

@app.route('/challenge', methods=['GET'])
def challenge():
    """
    Genera un challenge (reto) aleatorio para el usuario.
    El front end lo utilizará para que el usuario firme dicho reto.
    """
    username = request.args.get("username")
    if not username or username not in users:
        return jsonify({"error": "Usuario no encontrado."}), 404
    
    challenge_bytes = os.urandom(32)  # Reto de 256 bits
    challenge_b64 = base64.b64encode(challenge_bytes).decode('utf-8')
    # Almacenar el reto temporalmente en el registro del usuario
    users[username]["challenge"] = challenge_bytes
    return jsonify({"username": username, "challenge": challenge_b64})

@app.route('/login', methods=['POST'])
def login():
    """
    Verifica la autenticación de un usuario.
    Se espera un JSON con "username" y "signature" (firma del challenge).
    Se utiliza la clave pública almacenada para verificar la firma.
    """
    data = request.get_json()
    username = data.get("username")
    signature_b64 = data.get("signature")
    if not username or username not in users:
        return jsonify({"error": "Usuario no encontrado."}), 404
    if "challenge" not in users[username]:
        return jsonify({"error": "No se ha generado un challenge para este usuario."}), 400

    # Recuperar y eliminar el challenge (para evitar reuso)
    challenge_bytes = users[username].pop("challenge")
    signature = base64.b64decode(signature_b64)
    public_key = users[username]["public_key"]

    with oqs.Signature("Dilithium2") as verifier:
        valid = verifier.verify(challenge_bytes, signature, public_key)
    
    if valid:
        return jsonify({"message": "Autenticación exitosa."}), 200
    else:
        return jsonify({"error": "Firma inválida."}), 401

@app.route('/sign', methods=['POST'])
def sign_message():
    """
    Endpoint de demostración para firmar un mensaje usando la clave privada del usuario.
    En una aplicación real, esta operación se debería realizar en el lado del cliente.
    Se espera un JSON con "username" y "message" (mensaje en Base64).
    """
    data = request.get_json()
    username = data.get("username")
    message_b64 = data.get("message")
    if not username or username not in users:
        return jsonify({"error": "Usuario no encontrado."}), 404
    
    message = base64.b64decode(message_b64)
    secret_key = users[username]["secret_key"]
    
    with oqs.Signature("Dilithium2") as signer:
        signature = signer.sign(message, secret_key)
    
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    return jsonify({"username": username, "signature": signature_b64})

if __name__ == "__main__":
    # Ejecuta el servidor en modo debug para pruebas.
    app.run(debug=True)
