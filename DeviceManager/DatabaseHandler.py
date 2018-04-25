import os
from flask import g, request
from flask_sqlalchemy import SQLAlchemy

from .app import app
from .conf import CONFIG
from .utils import get_allowed_service

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = CONFIG.get_db_url()
app.config['SQLALCHEMY_BINDS'] = {}

# adapted from https://gist.github.com/miikka/28a7bd77574a00fcec8d
class MultiTenantSQLAlchemy(SQLAlchemy):
    def check_binds(self, bind_key):
        binds = app.config.get('SQLALCHEMY_BINDS')
        if binds.get(bind_key, None) is None:
            binds[bind_key] = CONFIG.get_db_url()
            app.config['SQLALCHEMY_BINDS'] = binds

    def choose_tenant(self, bind_key):
        if hasattr(g, 'tenant'):
            raise RuntimeError('Switching tenant in the middle of the request.')
        g.tenant = bind_key

    def get_engine(self, app=None, bind=None):
        if bind is None:
            if not hasattr(g, 'tenant'):
                raise RuntimeError('No tenant chosen.')
            bind = g.tenant
        self.check_binds(bind)
        return super().get_engine(app=app, bind=bind)

SINGLE_TENANT = os.environ.get('SINGLE_TENANT', False)
if SINGLE_TENANT:
    db = SQLAlchemy(app)
else:
    db = MultiTenantSQLAlchemy(app)

    @app.before_request
    def before_request():
        tenant = get_allowed_service(request.headers['authorization'])
        db.choose_tenant(tenant)
