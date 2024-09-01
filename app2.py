from flask import Flask, render_template, request, redirect, url_for, session
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

app = Flask(__name__)

# MongoDB connection URI
uri = "mongodb+srv://flask:Flask12345@cluster0.avyf6ln.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

# Select the database
db = client['myDB']  # Replace 'myDatabase' with the name of your database

app.secret_key = 'super secret key'


@app.route('/test_db_connection')
def test_db_connection():
    try:
        client.admin.command('ping')
        return "Database connection is working!"
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username =  request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the user already exists
        existing_user = db.users.find_one({"username": username})
        if existing_user is None:
            password_hash = generate_password_hash(password)
            new_user = {
                "username": username,
                "email": email,
                "password_hash": password_hash
            }
            db.users.insert_one(new_user)
            return redirect(url_for('login'))
        else:
            error = 'The username already exists. Please try again.'

    return render_template('register.html', error=error)

if __name__ == '__main__':
    app.run(debug=True)
