import os
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, messaging

app = Flask(__name__)

# Inicializar Firebase Admin SDK
if not firebase_admin._apps:
    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "serviceAccountKey.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "ProSecurity Backend Intermediario activo", "version": "1.0"})

@app.route("/webhook", methods=["POST"])
def webhook_dvr():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No se recibieron datos JSON"}), 400

        device_name = data.get("device_name", "Cámara de Seguridad")
        alert_message = data.get("message", "Se ha detectado movimiento o actividad sospechosa.")
        fcm_token = data.get("token")

        if not fcm_token:
            return jsonify({"error": "Falta el token FCM del dispositivo destino"}), 400

        message = messaging.Message(
            notification=messaging.Notification(
                title=f"Alerta: {device_name}",
                body=alert_message,
            ),
            token=fcm_token,
        )

        response = messaging.send(message)
        return jsonify({
            "success": True,
            "message_id": response,
            "info": "Notificación push enviada exitosamente al celular"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)