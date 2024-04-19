from flask import Flask, session, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash, generate_password_hash
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your_fallback_secret_key')

# Database connection details
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_NAME = os.environ.get('DB_NAME', 'sampledb')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASS = os.environ.get('DB_PASS', '123456')

def get_db_connection():
    """Establish a new connection to the database and return the connection."""
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        host=DB_HOST
    )
    return conn

@app.route('/')
def home():
    """Redirect to the login page if the user is not logged in."""
    if 'user' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('products'))

@app.route('/products')
def products():
    """Display the list of available products."""
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute("SELECT * FROM product")
        products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    """Add a product to the shopping cart."""
    quantity = request.form.get('quantity')
    code = request.form.get('code')

    # Input validation
    if not quantity or not code:
        flash('Invalid input', 'danger')
        return redirect(url_for('products'))

    try:
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError('Invalid quantity')
    except ValueError:
        flash('Invalid quantity', 'danger')
        return redirect(url_for('products'))

    # Database operations
    conn = get_db_connection()
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
        cursor.execute('SELECT * FROM product WHERE code = %s', (code,))
        product = cursor.fetchone()

    conn.close()

    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))

    # Managing cart
    cart = session.get('cart', {})
    if code in cart:
        cart[code]['quantity'] += quantity
        cart[code]['total_price'] = cart[code]['quantity'] * product['price']
    else:
        cart[code] = {
            'name': product['name'],
            'code': product['code'],
            'quantity': quantity,
            'price': product['price'],
            'total_price': quantity * product['price']
        }

    session['cart'] = cart
    flash(f'Added {quantity}x {product["name"]} to cart.', 'success')
    return redirect(url_for('products'))

def get_cart_items():
    """Retrieve cart items from the user's session."""
    return session.get('cart', {})

def calculate_total_cost(cart_items):
    """Calculate the total cost of items in the cart."""
    total_cost = 0.0  # Initialize total cost as a float to handle monetary values
    for item in cart_items.values():
        # Convert 'quantity' and 'price' to float
        quantity = float(item.get('quantity', 0))
        price = float(item.get('price', 0))
        
        # Calculate the total price for the item and add it to total cost
        total_cost += quantity * price
    
    return total_cost


def clear_cart():
    """Clear the user's cart by removing it from the session."""
    session.pop('cart', None)

@app.route('/empty_cart')
def empty_cart():
    """Empty the shopping cart."""
    session.pop('cart', None)
    flash('Cart has been emptied.', 'success')
    return redirect(url_for('products'))


@app.route('/delete_from_cart/<code>')
def delete_from_cart(code):
    """Remove a specific product from the cart."""
    cart = session.get('cart', {})
    if code in cart:
        cart.pop(code)
        session['cart'] = cart
        flash(f'Removed product with code {code} from cart.', 'success')
    else:
        flash('Product not found in cart.', 'danger')

    return redirect(url_for('products'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    """Handle the checkout process."""
    if request.method == 'POST':
        # Extract delivery address from the form
        delivery_address = request.form.get('delivery_address')
        
        # Get cart items from session
        cart_items = get_cart_items()
        
        # Calculate total cost
        total_cost = calculate_total_cost(cart_items)
        
        # Try placing the order
        try:
            place_order(cart_items, delivery_address, total_cost)
            
            # Clear user's cart after successful order placement
            clear_cart()
            
            # Redirect to order confirmation page
            return redirect(url_for('order_confirmation'))
        
        except Exception as e:
            # Log the exception for debugging purposes
            app.logger.error(f"Error placing order: {str(e)}")
            
            # Flash an error message to the user
            flash('There was an error placing your order. Please try again.', 'danger')
            
            # Redirect back to the checkout page
            return redirect(url_for('checkout'))

    # Handle GET request
    cart_items = get_cart_items()
    total_cost = calculate_total_cost(cart_items)
    
    return render_template('checkout.html', cart_items=cart_items, total_cost=total_cost)

@app.route('/order_confirmation')
def order_confirmation():
    """Render the order confirmation page."""
    return render_template('order_confirmation.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        password = request.form.get('password')

        # Check the user's credentials
        if check_password(username, password):
            # Start the user session
            session['user'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('products'))
        else:
            # Flash an error message for invalid credentials
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    # Render the login page if the request is GET or if the login fails
    return render_template('login.html')

def check_password(username, password):
    """Check the user's credentials."""
    # Define the hardcoded username and password hash for simplicity
    USERNAME = 'admin'
    PASSWORD_HASH = generate_password_hash('1234')
    
    if username == USERNAME and check_password_hash(PASSWORD_HASH, password):
        return True
    return False

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('user', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
