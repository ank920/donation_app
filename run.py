from app import create_app
import logging

app = create_app()

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)s] - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    # Enable SQLAlchemy query logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    
    app.run(debug=True)