from flask import Flask

from app.config import Config


def create_app() -> Flask:
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    from app.routes.dashboard import bp as dashboard_bp

    flask_app.register_blueprint(dashboard_bp)

    @flask_app.route("/")
    def index():
        from flask import redirect, url_for

        return redirect(url_for("dashboard.global_dashboard"))

    return flask_app
