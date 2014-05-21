import flask


def create_app():
    from cashman import models
    from cashman.views import views
    from cashman.admin import admin
    app = flask.Flask(__name__)

    app.config.from_pyfile('settings.py', silent=True)
    app.register_blueprint(views)
    app.register_blueprint(admin, url_prefix='/admin')
    models.db.init_app(app)
    return app
