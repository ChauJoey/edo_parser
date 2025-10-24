from quart import jsonify
from quart import request


class Response:

    @staticmethod
    def ok(data=None, message='Operation succeeded'):
        return jsonify({'success': True, 'data': data, 'message': message}), 200

    @staticmethod
    def badRequest(message='Bad request'):
        return jsonify({'success': False, 'message': message}), 200

    @staticmethod
    def unauthorized(message='Unauthorized'):
        return jsonify({'success': False, 'message': message}), 200

    @staticmethod
    def forbidden(message='Forbidden'):
        return jsonify({'success': False, 'message': message}), 200

    @staticmethod
    def notFound(message='Not found'):
        return jsonify({'success': False, 'message': message}), 200

    @staticmethod
    def error(message='Internal server error'):
        return jsonify({'success': False, 'message': message}), 200
