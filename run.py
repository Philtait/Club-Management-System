# File: run.py (root folder)

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)  # You can change debug to False in production
