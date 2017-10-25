import os
from base64 import a85encode

from flask import Flask, render_template, request, json, Response, abort

from PIL import Image, ImageSequence
from werkzeug.exceptions import UnsupportedMediaType

app = Flask(__name__)

DISPLAY_WIDTH = 144  # Width of the display
DISPLAY_HEIGHT = 24  # Height of the display
DEFAULT_DELAY  = 5000

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gif', methods=['POST'])
def gif():
    f = request.files['f']
    try:
        im = Image.open(f)
    except OSError:
        raise UnsupportedMediaType()
    # frames = []
    frames_info = []
    sequence_id = str(a85encode(os.urandom(4)))
    for frame_raw in ImageSequence.Iterator(im):
        frame_image, frame_info = process_frame(frame_raw, sequence_id)
        # frames.append(frame_image)
        frames_info.append(frame_info)
        # outputter.send_image(frame_image, frames_info)

    return Response(json.dumps({
        'frame_count': len(frames_info),
        'frames': frames_info,
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


def process_frame(frame_raw, sequence_id):
    frame = frame_raw.copy()
    if (DISPLAY_WIDTH, DISPLAY_HEIGHT) != frame.size:
        frame = frame.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    frame_image = frame.convert("L")
    frame_info = {
        'width_orig': frame_raw.width,
        'height_orig': frame_raw.height,
        'sequence_id': sequence_id,
        'duration': frame.info.get('duration', DEFAULT_DELAY),
        # 'data': repr([d for d in frame.tobytes()]),
    }
    return frame_image, frame_info


if __name__ == '__main__':
    app.config.from_object('defaults')
    app.config.from_pyfile('ledslie.cfg')
    app.run()

