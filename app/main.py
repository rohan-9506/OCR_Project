from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes
import base64, pika, os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

QUEUE = os.getenv("RABBITMQ_QUEUE")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")

def send_to_queue(image_bytes):
    connection = pika.BlockingConnection(pika.ConnectionParameters(RABBITMQ_HOST))
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE)
    channel.basic_publish(exchange='', routing_key=QUEUE, body=base64.b64encode(image_bytes))
    connection.close()

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file provided"}), 400

    if file.content_type == "application/pdf":
        image = convert_from_bytes(file.read())[0]
        image.save("temp.jpg", "JPEG")
        with open("temp.jpg", "rb") as f:
            image_bytes = f.read()
    elif "image" in file.content_type:
        image_bytes = file.read()
    else:
        return jsonify({"error": "Unsupported file type"}), 400

    send_to_queue(image_bytes)
    return jsonify({"message": "File sent for processing"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
