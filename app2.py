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

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        session['password'] = request.form['password']
        session['username'] = request.form['username']

        user = db.users.find_one({"username": session['username']})

        if user is None or not check_password_hash(user['password_hash'], session['password']):
            error = 'Incorrect username or password. Please try again.'
        else:
            session['username'] = user['username']
            return redirect(url_for('index'))

    return render_template('login.html', error=error)


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

@app.route('/')
def index():
    if 'username' in session and 'password' in session:
        current_user = db.users.find_one({"username": session['username']})

        books = db.books.aggregate([
            {
                '$match': {
                    'user_id': current_user['_id']
                }
            },
            {
                '$lookup': {
                    'from': 'authors',
                    'localField': 'author_id',
                    'foreignField': '_id',
                    'as': 'author'
                }
            },
            {
                '$lookup': {
                    'from': 'categories',
                    'localField': 'category_id',
                    'foreignField': '_id',
                    'as': 'category'
                }
            },
            {
                '$unwind': '$author'
            },
            {
                '$unwind': '$category'
            }
        ])

        books_list = list(books)

        return render_template('index.html', books=books_list)

    return redirect(url_for('login'))


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if 'username' in session:
        current_user = db.users.find_one({"username": session['username']})
        if request.method == 'POST':
            title = request.form['title']
            author_name = request.form['author']
            author_email = request.form['email']
            category_name = request.form['category']

            # Check if the author already exists
            author = db.authors.find_one({"email": author_email})
            if not author:
                author = {
                    "name": author_name,
                    "email": author_email
                }
                db.authors.insert_one(author)
                author_id = author['_id']
            else:
                author_id = author['_id']

            # Check if the category already exists
            category = db.categories.find_one({"name": category_name})
            if not category:
                category = {
                    "name": category_name
                }
                db.categories.insert_one(category)
                category_id = category['_id']
            else:
                category_id = category['_id']

            # Create the new book
            new_book = {
                "title": title,
                "author_id": author_id,
                "category_id": category_id,
                "user_id": current_user['_id']
            }
            db.books.insert_one(new_book)

            return redirect(url_for('index'))

        elif request.method == 'GET':
            authors = list(db.authors.find())
            categories = list(db.categories.find())
            return render_template('add.html', authors=authors, categories=categories)
    return redirect(url_for('login'))


@app.route('/edit_book/<id>', methods=['GET', 'POST'])
def edit_book(id):
    book = db.books.find_one({"_id": ObjectId(id)})  # Récupère le livre avec l'ID donné
    if request.method == 'POST':
        # Récupère les valeurs du formulaire
        title = request.form.get('title')
        author_name = request.form.get('author_name')
        author_email = request.form.get('author_email')
        category_name = request.form.get('category_name')

        # Cherche l'auteur existant ou crée un nouveau
        author = db.authors.find_one({"email": author_email})
        if not author:
            author = {
                "name": author_name,
                "email": author_email
            }
            db.authors.insert_one(author)

        # Cherche la catégorie existante ou crée une nouvelle
        category = db.categories.find_one({"name": category_name})
        if not category:
            category = {
                "name": category_name
            }
            db.categories.insert_one(category)

        # Met à jour le livre
        updated_book = {
            "title": title,
            "author_id": author['_id'],
            "category_id": category['_id']
        }
        db.books.update_one({"_id": ObjectId(id)}, {"$set": updated_book})

        return redirect(url_for('index'))

    # Récupère les données pour pré-remplir le formulaire
    authors = db.authors.find()
    categories = db.categories.find()

    return render_template('edit.html', book=book, authors=authors, categories=categories)


@app.route('/delete_book/<id>', methods=['POST'])
def delete_book(id):
    db.books.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
