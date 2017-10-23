from flask import Flask, render_template, request, redirect, url_for, json, Response, abort

from PIL import Image, ImageSequence

app = Flask(__name__)

DISPLAY_WIDTH = 144  # Width of the display
DISPLAY_HEIGHT = 24  # Height of the display


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/gif', methods=['POST'])
def gif():
    f = request.files['f']
    im = Image.open(f)
    frames = []
    frames_info = []
    for frame_raw in ImageSequence.Iterator(im):
        frame = frame_raw.copy()
        if (DISPLAY_WIDTH, DISPLAY_HEIGHT) != frame.size:
            frame = frame.resize((DISPLAY_WIDTH, DISPLAY_HEIGHT))
        frames.append(frame.convert("L"))
        frames_info.append({
            'width_orig': frame_raw.width,
            'height_orig': frame_raw.height,
            'duration': frame.info.get('duration', 5000),
            'data': repr([d for d in frame.tobytes()]),
        })

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

if __name__ == '__main__':
    app.run()
