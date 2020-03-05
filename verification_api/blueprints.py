# Import every blueprint file
from verification_api.views import general
from verification_api.views.v1 import verification


def register_blueprints(app):
    """Adds all blueprint objects into the app."""
    app.register_blueprint(general.general)
    app.register_blueprint(verification.verification_bp, url_prefix='/v1')

    # All done!
    app.logger.info("Blueprints registered")
