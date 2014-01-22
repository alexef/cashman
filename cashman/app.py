import flask


def create_app():
    from cashman import models
    from cashman.views import views
    app = flask.Flask(__name__)

    app.config.from_pyfile('settings.py', silent=True)
    app.register_blueprint(views)
    models.db.init_app(app)
    return app
