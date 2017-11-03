import os
from base64 import a85encode
from zlib import crc32

from PIL import Image, ImageSequence
import msgpack

from werkzeug.exceptions import UnsupportedMediaType
from flask import Flask, render_template, request, json, Response
from flask_mqtt import Mqtt


app = Flask(__name__)
mqtt = Mqtt()

DISPLAY_WIDTH = 144  # Width of the display
DISPLAY_HEIGHT = 24  # Height of the display
DEFAULT_DELAY  = 5000

@app.route('/')
def index():
    return render_template('index.html')


def send_image(seq_id, sequence):
    data = [seq_id, sequence]
    mqtt.publish('ledslie/sequences/1', msgpack.packb(data))


@app.route('/gif', methods=['POST'])
def gif():
    f = request.files['f']
    try:
        im = Image.open(f)
    except OSError:
        raise UnsupportedMediaType()
    sequence = []
    sequence_id = generate_id()
    for frame_nr, frame_raw in enumerate(ImageSequence.Iterator(im)):
        # frame_image, frame_info =
        sequence.append(process_frame(frame_raw))
    send_image(sequence_id, sequence)

    return Response(json.dumps({
        'frame_count': len(sequence),
        'frames': [f[1] for f in sequence],
    }), mimetype='application/json')


@app.route('/text', methods=['POST'])
def text1():
    text = request.form['text']
    duration = int(request.form['duration'])
    set_data = {
        'type': '1line',
        'text': text,
        'duration': duration}
    mqtt.publish('ledslie/typesetter/1', msgpack.packb(set_data))
    return Response(json.dumps(set_data), mimetype='application/json')


@app.route('/text3', methods=['POST'])
def text3():
    lines = request.form['l1'], request.form['l2'], request.form['l3']
    duration = int(request.form['duration'])
    set_data = {
        'type': '3lines',
        'lines': lines,
        'duration': duration
    }
    mqtt.publish('ledslie/typesetter/1', msgpack.packb(set_data))
    return Response(json.dumps(set_data), mimetype='application/json')


def process_frame(frame_raw):
    frame = frame_raw.copy()
    if (DISPLAY_WIDTH, DISPLAY_HEIGHT) != frame.size:
        frame = frame.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    frame_image = frame.convert("L")
    frame_info = {
        # 'id': generate_id(),
        # 'width_orig': frame_raw.width,
        # 'height_orig': frame_raw.height,
        'duration': frame.info.get('duration', DEFAULT_DELAY),
        # 'image_crc': crc32(frame_image.tobytes())
        # 'data': repr([d for d in frame.tobytes()]),
    }
    return frame_image.tobytes(), frame_info


def generate_id():
    return a85encode(os.urandom(4)).decode("ASCII")


if __name__ == '__main__':
    app.config.from_object('defaults')
    app.config.from_envvar('LEDSLIE_CONFIG')
    mqtt.init_app(app)
    app.run()

