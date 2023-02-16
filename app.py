from flask import Flask, Response, render_template
import io
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

@app.route('/eventWeekly')
def eventWeekly():
    fig = analysis.giveEventWeekly()
    return convertFigure(fig)

@app.route('/DTBookings')
def DTBookings():
    fig = analysis.giveTDeltaBookings()
    print('Sending graph...')
    return convertFigure(fig)

@app.route('/test')
def test():
    return Response('this is a test')
