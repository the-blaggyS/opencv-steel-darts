from typing import Callable, List, Optional

from flask import Flask, jsonify

from server.classes import Dart

app = Flask(__name__)

get_darts: Callable[[], List[Dart]]


@app.get('/calibrate')
def calibrate():
    return {'dbg': 'todo'}


@app.get('/darts')
def read_darts():
    darts: List[Optional[Dart]] = get_darts()
    return jsonify([dart.asjson() if dart else None for dart in darts])
