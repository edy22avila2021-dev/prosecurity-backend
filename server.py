import os
from flask import Flask, request, jsonify
# import firebase_admin
# from firebase_admin import credentials, messaging

app = Flask(__name__)

# NOTA PARA EL FUTURO: Descomenta estas líneas cuando tengas el archivo JSON de Firebase
# cred = credentials.Certificate("firebase-service-account.json")
# firebase_admin.initialize_app(cred)

# --- BASE DE DATOS DEL INSTALADOR (El Guardián) ---
# Por ahora está en memoria. Aquí defines qué DVRs están pagados 
# y EXACTAMENTE qué cámaras tienen permiso de usar la IA.
CLIENT_DATABASE = {
    "SN-123456789": {
        "client_name": "Local Comercial Centro",
        "is_active": True,            # Si al año no pagan, cambias esto a False y se apaga todo.
        "authorized_channels": [1, 2], # Solo autorizaste las cámaras 1 y 2.
        "fcm_token": "TOKEN_DEL_TELEFONO_DEL_CLIENTE"
    }
}

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "ProSecurity Backend Intermediario activo", 
        "version": "1.1",
        "mode": "Hybrid-SaaS"
    }), 200

@app.route('/api/webhook/alert', methods=['POST'])
def handle_dvr_alert():
    """
    Este es el Webhook. Aquí apuntarás la configuración de "Red -> HTTP/FTP"
    del grabador viejo del cliente.
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data received"}), 400

        # El grabador debe enviarte al menos estos datos
        device_sn = data.get("serial_number")
        channel = int(data.get("channel", -1))
        event_type = data.get("event_type", "motion")

        # 1. FILTRO DE SEGURIDAD (Aquí garantizas tu negocio)
        client = CLIENT_DATABASE.get(device_sn)
        
        if not client:
            print(f"Bloqueado: Equipo {device_sn} no existe en tu base de datos.")
            return jsonify({"status": "rejected", "reason": "Device not registered"}), 403
            
        if not client["is_active"]:
            print(f"Bloqueado: Licencia expirada para {device_sn}.")
            return jsonify({"status": "rejected", "reason": "License expired"}), 403

        if channel not in client["authorized_channels"]:
            # El cliente intentó activar una cámara por su cuenta sin pagarte.
            print(f"Bloqueado: La cámara {channel} del equipo {device_sn} no está pagada/autorizada.")
            return jsonify({"status": "rejected", "reason": "Channel not authorized for AI"}), 403

        # 2. PROCESAMIENTO DE IA (Arquitectura Híbrida)
        # Aquí procesaremos la foto que envíe el DVR para ver si es un humano o una falsa alarma.
        # Por ahora, simulamos que la IA detectó una amenaza real.
        ai_threat_detected = True 

        # 3. DISPARAR NOTIFICACIÓN AL TELÉFONO (FCM)
        if ai_threat_detected:
            fcm_token = client["fcm_token"]
            send_push_notification(fcm_token, device_sn, channel, event_type)

        return jsonify({"status": "success", "message": "Alerta procesada y enviada"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def send_push_notification(token, sn, channel, event_type):
    """ Función para despertar el teléfono del cliente mediante Firebase """
    
    # Cuando tengas el SDK de Firebase activo, este es el código que envía la alerta real:
    # 
    # message = messaging.Message(
    #     notification=messaging.Notification(
    #         title="🚨 Alerta ProSecurity",
    #         body=f"Detección confirmada por IA en Cámara {channel}"
    #     ),
    #     data={
    #         "action": "open_live_view",
    #         "device_sn": sn,
    #         "channel": str(channel)
    #     },
    #     token=token,
    #     android=messaging.AndroidConfig(
    #         priority='high', # Esto es vital para que suene aunque el celular esté bloqueado
    #         notification=messaging.AndroidNotification(
    #             sound='default',
    #             channel_id='prosecurity_high_alert'
    #         )
    #     )
    # )
    # try:
    #     response = messaging.send(message)
    #     print('Notificación enviada exitosamente:', response)
    # except Exception as e:
    #     print('Error al enviar la notificación:', e)
    
    print(f"\n[SIMULADOR ACTIVO] -> Disparando Notificación Push de Alta Prioridad.")
    print(f"Destino (Token): {token}")
    print(f"Mensaje: Alerta de IA en Equipo {sn}, Cámara {channel}\n")


if __name__ == '__main__':
    # Render asigna el puerto dinámicamente, por eso usamos os.environ
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
