import pika, base64, os
from extract import extract_form_data
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()
QUEUE = os.getenv("RABBITMQ_QUEUE")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

mongo_client = MongoClient(os.getenv("MONGODB_URI"))
mongo_db = mongo_client[os.getenv("MONGODB_DB")]
mongo_col = mongo_db[os.getenv("MONGODB_COLLECTION")]

def callback(ch, method, properties, body):
    image_bytes = base64.b64decode(body)
    result = extract_form_data(image_bytes)
    mongo_col.insert_one(result)
    print("✅ Inserted:", result)

connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
channel = connection.channel()
channel.queue_declare(queue=QUEUE)
channel.basic_consume(queue=QUEUE, on_message_callback=callback, auto_ack=True)

print("[*] Worker running...")
channel.start_consuming()
