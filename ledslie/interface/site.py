"""
    Ledslie, a community information display
    Copyright (C) 2017  Chotee@openended.eu

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

from PIL import Image, ImageSequence
import msgpack

from werkzeug.exceptions import UnsupportedMediaType
from flask import Flask, render_template, request, json, Response
from flask_mqtt import Mqtt

from ledslie.definitions import LEDSLIE_TOPIC_TYPESETTER_1LINE, LEDSLIE_TOPIC_TYPESETTER_3LINES, \
    LEDSLIE_TOPIC_SEQUENCES_PROGRAMS, LEDSLIE_TOPIC_SEQUENCES_UNNAMED

app = Flask(__name__)
mqtt = Mqtt()


@app.route('/')
def index():
    return render_template('index.html')


def send_image(sequence):
    mqtt.publish(LEDSLIE_TOPIC_SEQUENCES_UNNAMED, msgpack.packb(sequence))


@app.route('/gif', methods=['POST'])
def gif():
    f = request.files['f']
    try:
        im = Image.open(f)
    except OSError:
        raise UnsupportedMediaType()
    sequence = []
    for frame_nr, frame_raw in enumerate(ImageSequence.Iterator(im)):
        # frame_image, frame_info =
        sequence.append(process_frame(frame_raw))
    send_image(sequence)

    return Response(json.dumps({
        'frame_count': len(sequence),
        'frames': [f[1] for f in sequence],
    }), mimetype='application/json')


@app.route('/text', methods=['POST'])
def text1():
    text = request.form['text']
    duration = int(request.form['duration'])
    set_data = {
        'text': text,
        'duration': duration}
    mqtt.publish(LEDSLIE_TOPIC_TYPESETTER_1LINE, msgpack.packb(set_data))
    return Response(json.dumps(set_data), mimetype='application/json')


@app.route('/text3', methods=['POST'])
def text3():
    lines = request.form['l1'], request.form['l2'], request.form['l3']
    duration = int(request.form['duration'])
    set_data = {
        'lines': lines,
        'duration': duration
    }
    mqtt.publish(LEDSLIE_TOPIC_TYPESETTER_3LINES, msgpack.packb(set_data))
    return Response(json.dumps(set_data), mimetype='application/json')


def process_frame(frame_raw):
    frame = frame_raw.copy()
    if (app.config.get("DISPLAY_WIDTH"), app.config.get("DISPLAY_HEIGHT")) != frame.size:
        frame = frame.resize((app.config.get("DISPLAY_WIDTH"), app.config.get("DISPLAY_HEIGHT")))
    frame_image = frame.convert("L")
    frame_info = {
        # 'id': generate_id(),
        # 'width_orig': frame_raw.width,
        # 'height_orig': frame_raw.height,
        'duration': frame.info.get('duration', app.config.get("DISPLAY_DEFAULT_DELAY")),
        # 'image_crc': crc32(frame_image.tobytes())
        # 'data': repr([d for d in frame.tobytes()]),
    }
    return frame_image.tobytes(), frame_info


def make_app():
    app.config.from_object('ledslie.defaults')
    app.config.from_envvar('LEDSLIE_CONFIG')
    mqtt.init_app(app)
    print("broker url: %s. port: %s." % (mqtt.broker_url, mqtt.broker_port))
    return app


def main():
    site_app = make_app()
    site_app.run()


if __name__ == '__main__':
    main()
