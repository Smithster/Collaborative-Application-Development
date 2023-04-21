from flask import Flask, Response, render_template
import io
import json
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib import pyplot as plt
import data.analysis as analysis
import pandas as pd

app = Flask(__name__)


# Converts png image into bytes
def convertFigure(graph):
    output = io.BytesIO()
    FigureCanvasAgg(graph).print_png(output)
    return Response(output.getvalue(), 'image/png')


# Converts user inputs into data types more usable by the analysis file
def formatConstraints(data):
    try:
        data['StartDate'] = pd.to_datetime(data['StartDate'])
        data['FromDate'] = pd.to_datetime(data['FromDate'])
        data['GroupSize'] == int(data['GroupSize'])
    except:
        # this shoudn't occur thanks to input checking from JS file, but you never know
        print("Invalid Data Type")
        return
    return data


# Routing for the flask
@app.route('/')
def index():
    return render_template('graph.html')


@app.route('/prediction/<data>')
def getPrediction(data):
    constraints = json.loads(data)
    constraints = formatConstraints(constraints)
    fig = analysis.getPrediction(constraints)
    return convertFigure(fig)


# Allows the analysis file to return the event types that exist in the data
# for the user input
@app.route('/getEventTypes')
def getEventTypes():
    eventTypes = analysis.getEventTypes()
    eventTypes = json.dumps(eventTypes)
    return Response(eventTypes, 'application/json')