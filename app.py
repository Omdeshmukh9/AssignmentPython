from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt
import datetime

app = Flask(__name__)
app.secret_key = 'helloworld'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    price = db.Column(db.Float)
    photo = db.Column(db.BLOB)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Ensure database tables are created
with app.app_context():
    db.create_all()

# Route to add product
@app.route('/add_product', methods=['POST'])
def add_product_route():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        
        # Handle photo upload
        photo = None
        if 'photo' in request.files:
            photo_file = request.files['photo']
            if photo_file.filename != '':
                photo = photo_file.read()  # Read the file data as binary
                # You can optionally resize or process the image data here before storing
                
        # Create a new product instance with the provided data
        new_product = Product(name=name, description=description, price=price, photo=photo)
        
        # Add the new product to the database session and commit the changes
        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('index'))

@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        cart_items = session['cart']
        session['cart'] = [item for item in cart_items if item['id'] != product_id]
    return redirect(url_for('cart'))
    
@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if request.method == 'POST':
        product = Product.query.get(product_id)
        if 'cart' not in session:
            session['cart'] = []
        session['cart'].append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': product.price
        })
        return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = []
    total_amount = 0
    if 'cart' in session:
        product_ids = [item['id'] for item in session['cart']]
        cart_items = Product.query.filter(Product.id.in_(product_ids)).all()
        total_amount = sum(item.price for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total_amount=total_amount)

# Define routes
@app.route('/')
def index():
    products = Product.query.all()
    # Check if the user is logged in
    if 'token' in session:
        logged_in = True
    else:
        logged_in = False
    return render_template('index.html', products=products, logged_in=logged_in)

@app.route('/product')
def product():
    return render_template('product.html')

# Dummy database for storing user information
@app.route('/register', methods=['POST'])
def register1():
    if request.headers['Content-Type'] == 'application/json':
        data = request.json
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index')), 201

@app.route('/login', methods=['GET', 'POST'])
def login1():
    if request.method == 'POST':
        if request.headers['Content-Type'] == 'application/json':
            data = request.json
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400

        user = User.query.filter_by(username=username, password=password).first()
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401

        token = jwt.encode({'username': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.secret_key)
        session['token'] = token
        return redirect(url_for('index'))
    else:
        # Render the login page
        return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove the 'token' session variable to log out the user
    session.pop('token', None)
    return redirect(url_for('index'))

# Protected route that requires JWT authentication
@app.route('/protected', methods=['GET'])
def protected():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({'error': 'Token is missing'}), 401

    try:
        data = jwt.decode(token, app.secret_key)
        return jsonify({'message': 'You are logged in as {}'.format(data['username'])}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/register')
def register():
    # Render the register page
    return render_template('register.html')

# Route to display and delete products
@app.route('/delete', methods=['GET', 'POST'])
def delete_products():
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        product = Product.query.get(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
    products = Product.query.all()
    return render_template('delete.html', products=products)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    render_template('delete')

if __name__ == '__main__':
    app.run(debug=True)
