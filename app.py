import logging
import os

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask.ext.login import (
    LoginManager,
    UserMixin,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from flask_bootstrap import Bootstrap
from saml2 import (
    BINDING_HTTP_POST,
    BINDING_HTTP_REDIRECT,
    entity,
)
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
import requests

import pymysql

db = pymysql.connect(host='localhost',
                             user='root',
                             # password='123',
                             db='employees',
                             charset='utf8mb4',
                             cursorclass=pymysql.cursors.DictCursor)


metadata_url_for = {
    'example-okta-com': 'https://dev-946746.oktapreview.com/app/exkeumzkm4PT5pAcu0h7/sso/saml/metadata'
    }

app = Flask(__name__)
app.config.from_object('config')
Bootstrap(app)
login_manager = LoginManager()
login_manager.setup_app(app)
logging.basicConfig(level=logging.DEBUG)
user_store = {}

def saml_client_for(idp_name=None):
    if idp_name not in metadata_url_for:
        raise Exception("Settings for IDP '{}' not found".format(idp_name))
    acs_url = url_for(
        "idp_initiated",
        idp_name=idp_name,
        _external=True)
    https_acs_url = url_for(
        "idp_initiated",
        idp_name=idp_name,
        _external=True,
        _scheme='https')
    rv = requests.get(metadata_url_for[idp_name])
    settings = {
        'metadata': {
            'inline': [rv.text],
            },
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [
                        (acs_url, BINDING_HTTP_REDIRECT),
                        (acs_url, BINDING_HTTP_POST),
                        (https_acs_url, BINDING_HTTP_REDIRECT),
                        (https_acs_url, BINDING_HTTP_POST)
                    ],
                },
                'allow_unsolicited': True,
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
    }
    spConfig = Saml2Config()
    spConfig.load(settings)
    spConfig.allow_unknown_attributes = True
    saml_client = Saml2Client(config=spConfig)
    return saml_client


class User(UserMixin):
    def __init__(self, user_id):
        user = {}
        self.id = None
        self.first_name = None
        self.last_name = None
        try:
            user = user_store[user_id]
            self.id = unicode(user_id)
            self.first_name = user['first_name']
            self.last_name = user['last_name']
        except:
            pass


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route("/")
def main_page():
    return render_template('main_page.html', idp_dict=metadata_url_for)


@app.route("/saml/sso/<idp_name>", methods=['POST'])
def idp_initiated(idp_name):
    saml_client = saml_client_for(idp_name)
    authn_response = saml_client.parse_authn_request_response(
        request.form['SAMLResponse'],
        entity.BINDING_HTTP_POST)
    authn_response.get_identity()
    user_info = authn_response.get_subject()
    username = user_info.text

    if username not in user_store:
        user_store[username] = {
            'first_name': authn_response.ava['FirstName'][0],
            'last_name': authn_response.ava['LastName'][0],
            }
    user = User(username)
    session['saml_attributes'] = authn_response.ava
    login_user(user)
    url = url_for('user')
    if 'RelayState' in request.form:
        url = request.form['RelayState']
    return redirect(url)


@app.route("/saml/login/<idp_name>")
def sp_initiated(idp_name):
    saml_client = saml_client_for(idp_name)
    reqid, info = saml_client.prepare_for_authenticate()

    redirect_url = None
    for key, value in info['headers']:
        if key is 'Location':
            redirect_url = value
    response = redirect(redirect_url, code=302)
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route("/user")
@login_required
def user():
    return render_template('user.html', session=session)


@app.errorhandler(401)
def error_unauthorized(error):
    return render_template('unauthorized.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main_page"))

@app.route("/employee_data")
@login_required
def employee_data():
    return render_template('employee_data.html')

@app.route("/current_dept_emps")
@login_required
def current_dept_emps():
    cursor = db.cursor()
    sql = "SELECT * FROM current_dept_emp"
    cursor.execute(sql)
    current_dept_emps = cursor.fetchall()
    return render_template('current_dept_emps.html', current_dept_emps=current_dept_emps)

@app.route("/departments")
@login_required
def departments():
    cursor = db.cursor()
    sql = "SELECT * FROM departments"
    cursor.execute(sql)
    departments = cursor.fetchall()
    return render_template('departments.html', departments=departments)

@app.route("/dept_emps")
@login_required
def dept_emps():
    cursor = db.cursor()
    sql = "SELECT * FROM dept_emp"
    cursor.execute(sql)
    dept_emps = cursor.fetchall()
    return render_template('dept_emps.html', dept_emps=dept_emps)

@app.route("/dept_emp_latest_dates")
@login_required
def dept_emp_latest_dates():
    cursor = db.cursor()
    sql = "SELECT * FROM dept_emp_latest_date"
    cursor.execute(sql)
    dept_emp_latest_dates = cursor.fetchall()
    return render_template('dept_emp_latest_dates.html', dept_emp_latest_dates=dept_emp_latest_dates)

@app.route("/dept_managers")
@login_required
def dept_managers():
    cursor = db.cursor()
    sql = "SELECT * FROM dept_manager"
    cursor.execute(sql)
    dept_managers = cursor.fetchall()
    return render_template('dept_managers.html', dept_managers=dept_managers)

@app.route("/employees")
@login_required
def employees():
    cursor = db.cursor()
    sql = "SELECT * FROM employees"
    cursor.execute(sql)
    employees = cursor.fetchall()
    return render_template('employees.html', employees=employees)

@app.route("/salaries")
@login_required
def salaries():
    cursor = db.cursor()
    sql = "SELECT * FROM salaries"
    cursor.execute(sql)
    salaries = cursor.fetchall()
    return render_template('salaries.html', salaries=salaries)


@app.route("/titles")
@login_required
def titles():
    cursor = db.cursor()
    sql = "SELECT * FROM titles"
    cursor.execute(sql)
    titles = cursor.fetchall()
    return render_template('titles.html',titles=titles)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    if port == 5000:
        app.debug = True
    app.run(host='0.0.0.0', port=port)