import flask
import bcf

tmpl_dir = 'templates'
app = flask.Flask(__name__, template_folder=tmpl_dir)

from flask import request
from flask import redirect


@app.route('/', methods=['GET', 'POST'])
def find():
    return flask.render_template('hladaj.html', error=None)


@app.route('/find', methods=['GET', 'POST'])
def findRoutePage():
    ''' Returns page where user can input addresses for point A and B of their
        trip.'''
    if request.method == 'POST':
        frm = request.form['frm']
        to = request.form['where']
        routes = bcf.getRoutes(frm, to)

        if len(routes) == 0:
            error = 'Error: From/where is empty.'
            return flask.render_template('hladaj.html', error=error)

        route = bcf.getFirstRoute(frm, to)
        return foundRoutePage(frm, to, routes)


@app.route('/found')
def foundRoutePage(frm, to, result):
    ''' Returns page with found results for users trip. '''
    return flask.render_template('najdene.html', frm=frm, where=to,
                                 result=result, error=None)

if __name__ == '__main__':
    app.debug = True
    app.run()
