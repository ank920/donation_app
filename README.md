# Donation App

## Overview
The Donation App is a Flask-based web application designed to facilitate donations. It includes user authentication, email notifications, and a PostgreSQL database for data management.

## Features
- User registration and login
- Password reset via email
- Donation tracking
- Admin dashboard

## Technologies Used
- Flask
- Flask-Login
- Flask-Mail
- Flask-SQLAlchemy
- PostgreSQL
- Gunicorn
- PyJWT

## Setup Instructions

### Prerequisites
- Python 3.11
- PostgreSQL
- Git

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/donation_app.git
   cd donation_app
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up the environment variables in a `.env` file:
   ```
   FLASK_APP=run.py
   FLASK_ENV=production
   SECRET_KEY=your-secret-key
   DATABASE_URL=your-database-url
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-email-password
   ADMIN_EMAIL=your-email@gmail.com
   ```

5. Run the application:
   ```bash
   flask run
   ```

## Deployment
The app is deployed on Render. Ensure all environment variables are set in the Render dashboard and the PostgreSQL database is configured.

## Contributing
Feel free to submit issues or pull requests. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is licensed under the MIT License. 