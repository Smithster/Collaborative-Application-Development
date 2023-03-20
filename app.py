from flask import Flask, Response, render_template
import io
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pyplot as plt
import data.analysis as analysis
import pandas as pd

app = Flask(__name__)

def convertFigure(graph):
    output = io.BytesIO()
    FigureCanvasAgg(graph).print_png(output)
    return Response(output.getvalue(), 'image/png')

def formatConstraints(data):
    try:
        data['StartDate'] = pd.to_datetime(data['StartDate'])
        data['FromDate'] = pd.to_datetime(data['FromDate'])
        data['StartBookings'] = pd.to_datetime(data['StartDate'])
        data['GroupSize'] == int(data['GroupSize'])
    except:
        print("Invalid Data Type")
    return data
    
@app.route('/')
def index():
  return render_template('graph.html')

@app.route('/getConstraints')
def getConstraints():
    constraints = analysis.getHeaders()
    return Response(constraints, 'text/string')

@app.route('/prediction/<data>')
def getPrediction(data):
    constraints = json.loads(data)
    constraints = formatConstraints(constraints)
    fig = analysis.getPrediction(constraints)
    return convertFigure(fig)

@app.route('/getEventTypes')
def getEventTypes():
    eventTypes = analysis.getEventTypes()
    eventTypes = json.dumps(eventTypes)
    return Response(eventTypes, 'application/json')