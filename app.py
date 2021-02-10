from flask import Flask, request, jsonify

from datetime import datetime

from api import Api

app = Flask(__name__)

api = Api()

@app.route('/ticket/<string:ticket_number>', methods=['GET'])
def ticket(ticket_number):
    if request.method == 'GET':
        # Valida el boleto y en caso de ser válido envía el enlace
        # del streaming y el estatus del evento de streaming al cliente.
        return jsonify(api.validate_ticket(ticket_number))

    return jsonify({})

@app.route('/tickets/<string:event_id>',
           methods=['GET', 'POST'])
def tickets(event_id):
    if request.method == 'GET':
        return jsonify(api.get_tickets(event_id))
    elif request.method == 'POST':
        # Genera los boletos en Postgres y en Firestore
        # es llamado cuando la compra concluye.
        # Ejemplo:
        # {
        #   "event_id": "GLENNMILLERENCONCIERTO2020-02-0913:02",
        #   "customer": "Alberto Madrazo",
        #   "seats": [1, 2],
        #   "email_address": "info@betomad.com"
        # }
        api.generate_tickets(request.get_json())

    return jsonify({})

@app.route('/streaming_event/<string:event_id>',
           methods=['GET', 'PUT', 'PATCH'])
def streaming_event(event_id):
    if request.method == 'GET':
        api.get_streaming_event_details(event_id)
    elif request.method == 'PUT':
        # Actualizar evento de streaming
        # Se envían todos los campos
        # Ejemplo:
        # {
        #   "event_name": "Glenn Miller en concierto",
        #   "event_date": "2020-02-09 13:02",
        #   "streaming_link": "https://vimeo.com/nueva_id",
        #   "price": 500,
        #   "on_air": false
        # }
        api.update_streaming_event(event_id, request.get_json())
    elif request.method == 'PATCH':
        # Cambia el estado de un evento de streaming
        api.toggle_event_streaming(event_id)

    return jsonify({})

@app.route('/streaming_events', methods=['GET', 'POST'])
def streaming_events():
    if request.method == 'GET':
        # Obtiene una lista con todos los eventos de streaming
        return jsonify(api.get_streaming_events())

    # Crea un nuevo evento de streaming
    elif request.method == 'POST':
        # Crea un nuevo evento de streaming en Postgres y Firestore
        # Ejemplo:
        # {
        #   "event_name": "Glenn Miller en concierto",
        #   "event_date": "2020-02-09 13:02",
        #   "streaming_link": "https://vimeo.com/video_id",
        #   "price": 500,
        #   "on_air": false
        # }
        api.create_streaming_event(request.get_json())

    return jsonify({})

@app.route('/email_tickets/<string:event_id>', methods=['POST'])
def send_emails(event_id):
    if request.method == 'POST':
        # Enviar los correos de un evento de streaming
        # No implementé el envío porque es mejor utilizar el que 
        # ya se tiene actualmente
        return jsonify(api.email_tickets(event_id))

    return jsonify({})

@app.route('/')
def index():
    return jsonify({
        'status': 'OK!'
    })


if __name__ == '__main__':
    app.run(debug=True)
