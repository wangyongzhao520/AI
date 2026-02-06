from app import app
import os

if __name__ == '__main__':
    # Only enable debug in development environment
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
