from flask import Flask, Response, render_template
import io
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pyplot as plt
import data.analysis as analysis

app = Flask(__name__)

def convertFigure(graph):
    output = io.BytesIO()
    FigureCanvasAgg(graph).print_png(output)
    return Response(output.getvalue(), 'image/png')

@app.route('/')
def index():
  return render_template('graphPage.html')

@app.route('/getConstraints')
def getConstraints():
    constraints = analysis.getHeaders()
    return Response(constraints, 'text/string')

@app.route('/prediction/<constraints>')
def getPrediction(constraints):
    data = json.loads(constraints)
    fig = analysis.getPrediction(data)
    return convertFigure(fig)