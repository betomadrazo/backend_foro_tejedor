import psycopg2
from psycopg2.extras import RealDictCursor

from datetime import datetime
import random

from firestore import FirestoreStreaming

# Credenciales de Postgres
username = ''
password = ''
server = ''
database = ''


class Api:
    def get_streaming_event_details(self, event_id):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor(cursor_factory=RealDictCursor)

            q = "SELECT nombre_evento, id_evento, link_streaming, "\
                "precio, fecha_evento, al_aire "\
                f"FROM eventos_streaming WHERE id_evento='{event_id}' LIMIT 1"

            cur.execute(q)

            result = cur.fetchone()

            if result:
                return dict(result)

            return {}

        except Exception as e:
            print('Error:', e)

    def get_streaming_events(self):
        """Obtener una lista con todos los eventos
        """
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "SELECT * FROM eventos_streaming"

            cur.execute(q)

            streaming_events = cur.fetchall()

        except Exception as e:
            print('Error:', e)

        return streaming_events

    def create_streaming_event(self, data):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            event_name = data['event_name']
            event_date = data['event_date']
            streaming_link = data['streaming_link']
            price = data['price']
            on_air = data['on_air']

            event_id = (event_name + str(event_date)).upper().replace(' ', '')
            data['event_id'] = event_id

            q = "INSERT INTO eventos_streaming(" \
                "nombre_evento, id_evento, fecha_evento, "\
                "link_streaming, precio, al_aire)" \
                " VALUES('{}', '{}', '{}', '{}', {}, {})".format(
                    event_name, event_id, event_date,
                    streaming_link, price, on_air)

            cur.execute(q)
            conn.commit()

            # Genera un evento de streaming en Firestore
            firestore = FirestoreStreaming()
            firestore.set_streaming_event(data)

            return q

        except Exception as e:
            print('Error:', e)


    def update_streaming_event(self, event_id, data):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "UPDATE eventos_streaming SET " \
                "nombre_evento='{}', link_streaming='{}', "\
                "precio={}, fecha_evento='{}', al_aire={} "\
                "WHERE id_evento='{}'"\
                .format(data['event_name'], data['streaming_link'],
                        data['price'], data['event_date'], data['on_air'],
                        event_id)

            message = 'Evento actualizado'
            error = False

            cur.execute(q)
            conn.commit()

        except Exception as e:
            print('Error:', e)

    def toggle_event_streaming(self, event_id):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "UPDATE eventos_streaming SET " \
                "al_aire = NOT al_aire WHERE id_evento='{}'".format(event_id)

            cur.execute(q)
            conn.commit()

        except Exception as e:
            print('Error:', e)

    def validate_ticket(self, ticket_number):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "SELECT link_streaming, al_aire FROM eventos_streaming " \
                "WHERE id_evento=(" \
                "SELECT id_evento FROM boletos_streaming " \
                "WHERE numero_boleto='{}' LIMIT 1) LIMIT 1".\
                format(ticket_number)

            cur.execute(q)

            result = cur.fetchone()
            if result:
                return {'streaming_link': result[0], 'al_aire': result[1]}

            return {'error': 'Boleto no válido'}

        except Exception as e:
            print('Error:', e)

    def generate_tickets(self, data):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "SELECT fecha_evento, precio "\
                "FROM eventos_streaming "\
                "WHERE id_evento=\'{}\' LIMIT 1".format(data['event_id'])

            cur.execute(q)

            event_date, ticket_price = cur.fetchone()
            event_date = event_date.strftime('%Y-%m-%d %H:%M')

            tickets = data['seats']
            tickets_data = []

            iterated_q = ''

            # Cada boleto es un diccionario aparte
            for ticket in tickets:
                # Este número lo genera aleatoriamente
                # Si es necesario, cambiarlo por un patrón que tenga
                # más sentido
                ticket_number = str(random.randint(10000000, 99999999))

                tickets_data.append({
                    'ticket_number': ticket_number, 'seat': ticket})

                iterated_q += "('{}', '{}', '{}', {}, '{}', {}, '{}'),".format(
                    data['customer'], data['email_address'],
                    ticket_number, True, event_date, ticket, data['event_id'])

            # Borra la última coma (,)
            iterated_q = iterated_q[:-1]

            q = "INSERT INTO boletos_streaming("\
                "comprador, email, numero_boleto, activo, "\
                "fecha_evento, asiento, id_evento) "\
                "VALUES{}".format(iterated_q)

            cur.execute(q)
            conn.commit()

            ticket_data = {
                'event_id': data['event_id'],
                'tickets_data': tickets_data,
                'email_address': data['email_address'],
                'event_date': event_date,
                'ticket_price': ticket_price,
            }

            firestore = FirestoreStreaming()
            firestore.generate_ticket(ticket_data)

        except Exception as e:
            print('Error:', e)

    def get_tickets(self, event_id):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "SELECT comprador, email, numero_boleto, asiento "\
                "FROM boletos_streaming "\
                "WHERE id_evento='{}' ORDER BY email, asiento".format(event_id)

            cur.execute(q)
            result = cur.fetchall()

            tickets = []
            if result:
                customer = {}
                for record in result:
                    if 'email' in customer:
                        if customer['email'] != record[1]:
                            tickets.append(customer)
                            customer = self.add_new_array(record)
                        else:
                            customer['boletos'].append({
                                'numero_boleto': record[2],
                                'asiento': record[3]
                                }
                            )
                    else:
                        customer = self.add_new_array(record)
                tickets.append(customer)

            return tickets

        except Exception as e:
            print('Error:', e)

    def add_new_array(self, record):
        return {
            'comprador': record[0],
            'email': record[1],
            'boletos': [
                {
                    'numero_boleto': record[2],
                    'asiento': record[3]
                }
            ]
        }

    def email_tickets(self, event_id):
        event_info = self.get_streaming_event_details(event_id)

        if event_info:
            tickets = self.get_tickets(event_id)

            streaming_event_page = 'https://betomad.com/tejedor'
            failed_emails = []
            subject = 'Tus boletos para {}'.format(event_info['nombre_evento'])

            for customer in tickets:
                customer_name = customer['comprador']
                customer_email = customer['email']
                email_message = 'Hola, {}, '\
                    'estos son tus boletos para {} este {}\n'\
                    .format(customer_name, event_info['nombre_evento'],
                            event_info['fecha_evento'])

                email_info = {
                    'name': customer_name,
                    'email': customer_email,
                    'subject': subject,
                    'email_body': email_message
                }

                # En esta función es donde se envía el correo
                # 
                email_status = send_tickets(email_info)

                if email_status['error']:
                    failed_emails.append(customer)
                else:
                    self.mark_tickets_as_sent(customer_email, event_id)

            if failed_emails and (len(failed_emails) == len(tickets)):
                return {'error': True,
                        'message': 'No se enviaron todos los correos'}
            elif failed_emails and (len(failed_emails) != len(tickets)):
                return {'error': True,
                        'message': 'No se enviaron todos los correos'}
            return {'message': 'Mensajes enviados'}

        return {'error': True, 'message': 'Al parecer, el evento no existe.'}

    def mark_tickets_as_sent(self, customer_email, event_id):
        try:
            conn = psycopg2.connect(
                database=database, user=username, password=password)
            cur = conn.cursor()

            q = "UPDATE boletos_streaming SET recibio_boletos=TRUE "\
                "WHERE email='{}' AND id_evento='{}'"\
                .format(customer_email, event_id)

            cur.execute(q)
            conn.commit()

        except Exception as e:
            print('Error:', e)


def send_tickets(email_info):
    """Envía con el servidor de correos que ya se tiene.
    """
    return {'error': False}