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
        frame_image, frame_info = process_frame(frame_raw)
        sequence.append([frame_image, frame_info])
    send_image(sequence_id, sequence)

    return Response(json.dumps({
        'frame_count': len(sequence),
        'frames': [f[1] for f in sequence],
    }), mimetype='application/json')

    # return Response(json.dumps({
    #     # 'meta': str(frames[0].meta),
    #     'nr_of_frames': len(frames),
    # #     'frame_durations': [(i, f.meta['duration']) for i, f in enumerate(frames)],
    # #     'shape': frames[0].shape,
    #     'format': im.format,
    #     # 'palette': im.getpalette(),
    #     'mode': frames[0].mode,
    #     'width': frames[0].width,
    #     'height': frames[0].height,
    #     'frame_durations': [(i, f.info['duration']) for i, f in enumerate(frames)],
    #     'palette_size': int(len(im.getpalette())/3),
    #     'bytes_size': len(frames[0].tobytes()),
    #     'bytes': repr(frames[0].tobytes()),
    #     'data_size': len([d for d in frames[0].getdata()]),
    #     'data': repr([d for d in frames[0].getdata()]),
    #     'histogram': repr(frames[0].histogram()),
    #     'palette': repr(frames[0].getpalette()),
    # }), mimetype='application/json')


def process_frame(frame_raw):
    frame = frame_raw.copy()
    if (DISPLAY_WIDTH, DISPLAY_HEIGHT) != frame.size:
        frame = frame.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    frame_image = frame.convert("L")
    frame_info = {
        'id': generate_id(),
        'width_orig': frame_raw.width,
        'height_orig': frame_raw.height,
        'duration': frame.info.get('duration', DEFAULT_DELAY),
        'image_crc': crc32(frame_image.tobytes())
        # 'data': repr([d for d in frame.tobytes()]),
    }
    return frame_image.tobytes(), frame_info


def generate_id():
    return a85encode(os.urandom(4)).decode("ASCII")


if __name__ == '__main__':
    app.config.from_object('defaults')
    app.config.from_pyfile('ledslie.cfg')
    mqtt.init_app(app)
    app.run()

