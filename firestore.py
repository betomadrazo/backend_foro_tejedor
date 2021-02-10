from datetime import datetime

import firebase_admin
from firebase_admin import credentials, firestore

# el fichero firebase.json tiene las credenciales
cred = credentials.Certificate('firebase.json')
firebase_admin.initialize_app(cred)
db = firestore.client()


class FirestoreStreaming:
    """Base de datos Firestore para saber en "tiempo real" si el mismo boleto
       está siendo utilizado en más de un dispositivo.
    """

    def set_streaming_event(self, data):
        """Crea un evento de streaming
        """
        events_ref = db.collection('streamingEvents')
        q = events_ref.document(data['event_id']).set({
            u'id_evento': data['event_id'],
            u'nombre_evento': data['event_name'],
            u'fecha_evento': data['event_date'],
            u'precio': data['price'],
            u'link_streaming': data['streaming_link'],
            u'createdAt': firestore.SERVER_TIMESTAMP
        })

        # Si se creó el evento, registrarlo en la base de datos
        return q

    # Método para generar un boleto en Firestore
    def generate_ticket(self, data):
        """Genera los boletos que se hayan comprado en una orden
        """
        tickets_ref = db.collection('boletos_streaming')

        batch = db.batch()

        # Genera 1 boleto en firebase por cada boleto comprado
        for t in range(len(data['tickets_data'])):
            ticket_data = {
                u'boleto': data['tickets_data'][t]['ticket_number'],
                u'asiento': data['tickets_data'][t]['seat'],
                u'fecha_evento': data['event_date'],
                u'precio': data['ticket_price'],
                u'id_evento': data['event_id'],
                u'correo': data['email_address'],
                u'createdAt': firestore.SERVER_TIMESTAMP,
                u'token': '',
                u'desde_foro': True,
            }
            tickets_ref.document(
                data['tickets_data'][t]['ticket_number']).set(ticket_data)

        batch.commit()
