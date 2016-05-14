#!/usr/bin/python3

from bcf import get_coordinates, get_address, find
from flask import Flask, request, render_template, abort, redirect, url_for, g

tmpl_dir = 'templates'
static_dir = 'static'
app = Flask(__name__, template_folder=tmpl_dir, static_folder=static_dir)
print(app.static_folder)


@app.route('/', methods=['GET', 'POST'])
@app.route('/find', methods=['GET', 'POST'])
def find_route_page():  # noqa
    """
    Return page where user can input addresses for point A and B of their trip.
    """
    if request.method == 'POST':
        frm = request.form['frm']
        to = request.form['to']
        if len(frm) < 1 and len(to) < 1:
            e = 'Input data missing. Enter from and where you are travelling.'
            return render_template('hladaj.html', error=e)
        elif len(frm) < 1 and len(to) > 0:
            e = 'Input data missing. Enter from where you are travelling.'
            return render_template('hladaj.html', error=e)
        elif len(frm) > 0 and len(to) < 1:
            e = 'Input data missing. Enter where to you are travelling.'
            return render_template('hladaj.html', error=e)

        frm_c = get_coordinates(frm)
        to_c = get_coordinates(to)
        if frm_c is None and to_c is None:
            e = 'Input data invalid. Enter real "from" and "to" addresses.'
            return render_template('hladaj.html', error=e)
        if frm_c is None:
            e = 'Input data invalid. Enter real "from" addresses.'
            return render_template('hladaj.html', error=e)
        if to_c is None:
            e = 'Input data invalid. Enter real "to" addresses.'
            return render_template('hladaj.html', error=e)
        return found_route_page(frm, to)
    return render_template('hladaj.html')


@app.route('/found')
def found_route_page():
    """Return page with found routes for users trip."""
    frm = request.args.get('frm')
    to = request.args.get('to')
    alt = request.args.get('alt', '0')

    try:
        alt = int(alt)
    except:
        abort(400)
    if frm is None or to is None:
        abort(400)

    if len(frm) < 1 and len(to) < 1:
        g.e = 'Input data missing. Enter from and where you are travelling.'
        return redirect(url_for('find_route_page'))
    elif len(frm) < 1 and len(to) > 0:
        g.e = 'Input data missing. Enter from where you are travelling.'
        return redirect(url_for('find_route_page'))
    elif len(frm) > 0 and len(to) < 1:
        g.e = 'Input data missing. Enter where to you are travelling.'
        return redirect(url_for('find_route_page'))

    if frm.replace(' ', '').replace('.', '').replace(',', '').isdigit():
        frm_c = '({})'.format(frm)
        frm = get_address(frm_c)
    else:
        frm_c = get_coordinates(frm)
    to_c = get_coordinates(to)

    if frm_c is None and to_c is None:
        g.e = 'Input data invalid. Enter real "from" and "to" addresses.'
        return redirect(url_for('find_route_page'))
    if frm_c is None:
        g.e = 'Input data invalid. Enter real "from" addresses.'
        return redirect(url_for('find_route_page'))
    if to_c is None:
        g.e = 'Input data invalid. Enter real "to" addresses.'
        return redirect(url_for('find_route_page'))

    routes = find(frm, to)
    if routes is not None:
        return render_template('najdene.html', routes=routes, alt=alt, frm=frm,
                               to=to)
    else:
        e = 'Could not find any routes.'
        return render_template('najdene.html', error=e)


if __name__ == '__main__':
    app.debug = True
    app.run()
