import pika, json
from ..logger import logger

def listen_to_queue(rabbitmq_user, rabbitmq_pass, rabbitmq_host, rabbitmq_port, rabbitmq_queue, handle_command):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host,
                                                                   port=int(rabbitmq_port),
                                                                   virtual_host='/',
                                                                   credentials=pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)))
    channel = connection.channel()

    channel.queue_declare(queue=rabbitmq_queue, durable=True)

    def callback(ch, method, properties, body):
        try:
            # This function will be called when a message is received
            # body variable contains queue message data

            # Decode the message body
            message = json.loads(body.decode())

            pattern = message.get('pattern')

            # Extract the command from the message
            command = pattern.get("cmd")

            # Extract the data from the message
            data = message.get("data")

            # Handle the command and get the response
            response = handle_command(command, data)

            # Get the reply_to queue from message properties
            reply_to = properties.reply_to

            ch.basic_publish(exchange='', routing_key=reply_to,
                    properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                    body=json.dumps(response))
        except Exception as e:
            logger.exception(e)

    # Start consuming messages
    channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=True)

    logger.debug('Waiting for messages. To exit, press CTRL+C')
    channel.start_consuming()
