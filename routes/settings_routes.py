from flask import jsonify, request
from app import app
from models import db, Settings

@app.route('/api/settings', methods=['GET'])
def get_settings():
    settings = Settings.get_settings()
    return jsonify({
        'square_environment': settings.square_environment,
        'show_square_id_controls': settings.show_square_id_controls,
        'show_square_image_id_controls': settings.show_square_image_id_controls
    })
