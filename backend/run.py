import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
    
    # Run the application
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True
    )
