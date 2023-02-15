import flask
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg
import data.analysis as analysis

app = flask.Flask(__name__)

def convertFigure(graph):
    output = io.BytesIO()
    FigureCanvasAgg(graph).print_png(output)
    return Response(output.getvalue(), 'image/png')

@app.route('/')
def index():
  return flask.render_template('graphPage.html') 

@app.route('/eventWeekly')
def eventWeekly():
    fig = analysis.giveEventWeekly()
    return convertFigure(fig)

@app.route('/DTBookings')
def DTBookings():
    fig = analysis.giveTDeltaBookings()
    print('Sending graph...')
    return giveTDeltaBookins(fig)