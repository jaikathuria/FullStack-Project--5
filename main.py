# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#                   Importing App Dependencies
# ---------------------------------------------------------------------
from flask import Flask, render_template, request, redirect, url_for, \
    session, make_response, jsonify

import random
import string
from oauth2client.client import flow_from_clientsecrets, \
    FlowExchangeError, AccessTokenCredentials
import httplib2
import json
import requests

# Import SQLAlchemy

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# Import DB Modules

from db_setup import Base, User, Genre, Songs


# ---------------------------------------------------------------------
#                         App configration
# ---------------------------------------------------------------------
app = Flask(__name__)

# create engine connection with sql library

engine = create_engine('sqlite:///MusicDatabase.db')

# bind the engine with base class

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
conn = DBSession()

# Google Client ID.

CLIENT_ID = json.loads(open('client_secret.json', 'r').read(
))['web']['client_id']
APPLICATION_NAME = 'ItemCatalog'


# ------------------------------------------------------------------
#                      Helper  Functions
# ------------------------------------------------------------------

def redirect_url(default='index'):

    # redirect to the previous_url without error

    return request.args.get('next') or request.referrer \
        or url_for('genreListView')


def previous_url(error=False):

    # redirect to the previous_url with error

    if error:
        return redirect_url() + '?error=' + error
    return redirect_url()


def check_user():
    email = session['email']
    return conn.query(User).filter_by(email=email).one_or_none()


def add_user():
    user = User()
    user.name = session['name']
    user.email = session['email']
    user.url = session['img']
    user.provider = session['provider']
    conn.add(user)
    conn.commit()


def create_state():
    state = ''.join(random.choice(
                    string.ascii_uppercase + string.digits) for (
                    x) in xrange(
                    32))
    session['state'] = state
    return state


# ---------------------------------------------------------------------
#                           App Routes
# ---------------------------------------------------------------------

@app.route('/')
def genreListView():

    # Get Handler for the Main Page

    genreList = conn.query(Genre).all()
    state = create_state()
    return render_template('genreList.html', genres=genreList,
                           state=state)


@app.route('/genre/<int:gid>/')
def genreView(gid):

    # Get Handler for the Category Page.

    genre = conn.query(Genre).filter_by(id=gid).one()
    songList = conn.query(Songs).filter_by(g_id=gid)
    state = create_state()
    return render_template('genre.html', songs=songList, genre=genre,
                           state=state)


@app.route('/new/', methods=['get', 'post'])
def newSong():
    if request.method == 'POST':

        # Check if the request is post request or get.

        if 'provider' in session and session['provider'] != 'null':

            # Validates if user is logged or not.

            name = request.form['name']
            desc = request.form['desc']
            url = request.form['url']
            url = url.replace('watch?v=', 'embed/')
            url = url.replace('https://', '//')
            g_id = request.form['genre']

            # get the all variables from the post request.

            u_id = check_user().id
            if name and url and g_id:

                # Null/None Validation for name url and g_id.

                song = Songs()
                song.name = name
                song.g_id = g_id
                song.url = url
                song.u_id = u_id
                if desc:

                    # Check if description is also posted.

                    song.description = desc
                conn.add(song)
                conn.commit()
                return redirect(url_for('genreView', gid=g_id))
            else:
                return redirect(url_for('newSong',
                                error='incompletefields'))
        else:
            return redirect(previous_url('notLogged'))
    if 'provider' in session and session['provider'] != 'null':

        # Validates if user is logged or not.

        genreList = conn.query(Genre).all()
        state = create_state()
        return render_template('edit.html', genres=genreList,
                               state=state)
    else:
        return redirect(previous_url('notLogged'))


@app.route('/edit/g/<int:g_id>/s/<int:s_id>', methods=['get', 'post'])
def editSong(g_id, s_id):
    if request.method == 'POST':

        # Check if the request is post request or get.

        if 'provider' in session and session['provider'] != 'null':

            # Validates if user is logged or not.

            name = request.form['name']
            desc = request.form['desc']
            url = request.form['url']
            url = url.replace('watch?v=', 'embed/')
            url = url.replace('https://', '//')
            gid = request.form['genre']
            u_id = check_user().id
            if name and url and gid:

                # Null/None Validation for name url and g_id.

                song = conn.query(Songs).filter_by(id=s_id,
                                                   g_id=g_id).one_or_none()
                if song:

                    # Check if song exsists.

                    if song.u_id == u_id:

                        # Validates song ownership.

                        song.name = name
                        song.g_id = gid
                        song.url = url
                        if desc:

                            # Check if description is also posted.

                            song.description = desc
                        conn.add(song)
                        conn.commit()
                        return redirect(url_for('genreView', gid=gid))
                    else:
                        return redirect(url_for('genreListView',
                                                error='wrongOwner'))
                else:
                    return redirect(url_for('genreListView',
                                    error='dataNotFound'))
            else:
                return redirect(url_for('newSong',
                                error='incompleteFields'))
        else:
            return redirect(previous_url('notLogged'))
    else:

        # get Handler post.

        if 'provider' in session and session['provider'] != 'null':

            # Validates if user is logged or not.

            state = create_state()
            u_id = check_user().id
            genreList = conn.query(Genre).all()
            song = conn.query(Songs).filter_by(id=s_id,
                                               g_id=g_id).one_or_none()
            if song.u_id == u_id:

                # Validates song ownership.

                return render_template('edit.html', genres=genreList,
                                       song=song, state=state)
            else:
                return redirect(url_for('genreListView',
                                error='wrongOwner'))
        else:
            return redirect(previous_url('notLogged'))


@app.route('/delete/g/<int:g_id>/s/<int:s_id>')
def deleteSong(g_id, s_id):
    if 'provider' in session and session['provider'] != 'null':

        # Validates if user is logged or not.

        u_id = check_user().id
        song = conn.query(Songs).filter_by(id=s_id,
                                           g_id=g_id).one_or_none()
        if song:

            # Check if song exsists.

            if song.u_id == u_id:

                # Validates song ownership.

                conn.delete(song)
                conn.commit()
                return redirect(url_for('genreView', gid=g_id))
            else:
                return redirect(url_for('genreListView',
                                error='wrongOwner'))
        else:
            return redirect(url_for('genreListView',
                            error='dataNotFound'))
    else:
        return redirect(previous_url('notLogged'))


@app.route('/view/g/<int:g_id>/s/<int:s_id>')
def viewSong(g_id, s_id):
    song = conn.query(Songs).filter_by(id=s_id, g_id=g_id).one_or_none()
    if song:

        # Check if song exsists.

        state = create_state()
        return render_template('view.html', song=song, state=state)
    else:
        return redirect(url_for('genreListView', error='dataNotFound'))


# ------------------------------------------------------------------
#                     JSON Endpoints
# ------------------------------------------------------------------

@app.route('/genre.json')
def genreListJson():
    genreList = conn.query(Genre).all()
    return jsonify(genres=[genre.serialize for genre in genreList])


@app.route('/genre/<int:gid>.json')
def songListJson(gid):
    songList = conn.query(Songs).filter_by(g_id=gid)
    return jsonify(songs=[song.serialize for song in songList])


@app.route('/genre/<int:g_id>/song/<int:s_id>.json')
def songJson(g_id, s_id):
    song = conn.query(Songs).filter_by(id=s_id, g_id=g_id).one_or_none()
    return jsonify(song=song.serialize)


@app.route('/gconnect', methods=['post'])
def gConnect():
    if request.args.get('state') != session['state']:
        response.make_response(json.dumps('Invalid State paramenter'),
                               401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code

    code = request.data
    try:

        # Upgrade the authorization code into a credentials object

        oauth_flow = flow_from_clientsecrets('client_secret.json',
                                             scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = \
            make_response(json.dumps(
                'Failed to upgrade the authorisation code'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.

    access_token = credentials.access_token
    url = \
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' \
        % access_token
    header = httplib2.Http()
    result = json.loads(header.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']

    # Verify that the access token is used for the intended user.

    if result['user_id'] != gplus_id:
        response = make_response(
                                 json.dumps(
                                            "Token's user ID  " + """does not
match given user ID."""),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.

    if result['issued_to'] != CLIENT_ID:
        response = \
            make_response(json.dumps(
                                     "Token's client ID" + """does not
                                      match app's."""),
                          401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.

    stored_credentials = session.get('credentials')
    stored_gplus_id = session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = \
            make_response(json.dumps('Current user is already connected.'),
                          200)
        response.headers['Content-Type'] = 'application/json'
        return response
    session['credentials'] = access_token
    session['id'] = gplus_id

    # Get user info

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    # ADD PROVIDER TO LOGIN SESSION

    session['name'] = data['name']
    session['img'] = data['picture']
    session['email'] = data['email']
    session['provider'] = 'google'
    if not check_user():
        add_user()
    return jsonify(name=session['name'], email=session['email'],
                   img=session['img'])


@app.route('/fbconnect', methods=['post'])
def fbConnect():
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps({'state': 'invalidState'}),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    app_id = json.loads(open('client_secret_fb.json',
                             'r').read())['web']['app_id']
    app_secret = json.loads(open('client_secret_fb.json',
                                 'r').read())['web']['app_secret']
    url = """https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s""" % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API

    userinfo_url = 'https://graph.facebook.com/v2.4/me'

    # strip expire tag from access token

    token = result.split('&')[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' \
        % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    session['provider'] = 'facebook'
    session['name'] = data['name']
    session['email'] = data['email']
    session['id'] = data['id']
    stored_token = token.split('=')[1]
    session['credentials'] = stored_token

    # Get user picture

    url = """https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&
    height=150&
    width=150
    """ % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    session['img'] = data['data']['url']

    if not check_user():
        add_user()

    return jsonify(name=session['name'], email=session['email'],
                   img=session['img'])


@app.route('/logout', methods=['post'])
def logout():

    # Disconnect based on provider

    if session.get('provider') == 'google':
        return Gdisconnect()
    elif session.get('provider') == 'facebook':
        return FBdisconnect()
    else:
        response = make_response(json.dumps({'state': 'notConnected'}),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/fbdisconnect')
def FBdisconnect():
    f_id = session['id']
    access_token = session['credentials']

    # The access token must me included to successfully logout

    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' \
        % (f_id, access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]

    # Reset the user's session.

    del session['credentials']
    del session['id']
    del session['name']
    del session['email']
    del session['img']
    session['provider'] = 'null'
    response = make_response(json.dumps({'state': 'loggedOut'}), 200)
    response.headers['Content-Type'] = 'application/json'
    return response


@app.route('/gdisconnect')
def Gdisconnect():
    print 'gdisconnect'
    access_token = session['credentials']

    # Only disconnect a connected user.

    if access_token is None:
        print 'Access Token is None'
        response = make_response(json.dumps({'state': 'notConnected'}),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
        % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    print 'result is '
    print result
    if result['status'] == '200':

        # Reset the user's session.

        del session['credentials']
        del session['id']
        del session['name']
        del session['email']
        del session['img']
        session['provider'] = 'null'
        response = make_response(json.dumps({'state': 'loggedOut'}),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:

        # The given token was invalid, unable to revoke token

        response = make_response(json.dumps({'state': 'errorRevoke'}),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.secret_key = 'itstimetomoveon'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
