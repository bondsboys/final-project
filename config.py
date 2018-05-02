import os
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://trinitydev:trinitypass123@localhost/employees')
SQLALCHEMY_TRACK_MODIFICATIONS = False
WTF_CSRF_ENABLED = False # This option enables cross-site forgery prevention (makes more secure)
SECRET_KEY = 'bondsboys' # used to create a cryptographic token used to validate forms, only needed when CSRF enabled,