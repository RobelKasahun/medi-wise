# import create_app function from the app module
from app import create_app

# create Flask app
app = create_app()

# run the app if the file is main
if __name__ == '__main__':
    app.run(debug=True, port=8000)