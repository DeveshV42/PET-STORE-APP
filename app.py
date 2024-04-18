from flask import Flask, session, render_template, request, redirect, url_for,g,flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
 
app = Flask(__name__)
 
app.secret_key = "cairocoders-ednalan"
 
DB_HOST = "localhost"
DB_NAME = "sampledb"
DB_USER = "postgres"
DB_PASS = "123456"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)

 
@app.route('/')
def products():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
    cursor.execute("SELECT * FROM product")
    rows = cursor.fetchall()
    return render_template('products.html', products=rows)
 
@app.route('/add', methods=['POST'])
def add_product_to_cart():
    _quantity = int(request.form['quantity'])
    _code = request.form['code']
    # validate the received values
    if _quantity and _code and request.method == 'POST':
 
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
        cursor.execute('SELECT * FROM product WHERE code = %s', (_code,))
        row = cursor.fetchone()
                 
        itemArray = { row['code'] : {'name' : row['name'], 'code' : row['code'], 'quantity' : _quantity, 'price' : row['price'], 'image' : row['image'], 'total_price': _quantity * row['price']}}
                 
        all_total_price = 0
        all_total_quantity = 0
                 
        session.modified = True
        if 'cart_item' in session:
            if row['code'] in session['cart_item']:
                for key, value in session['cart_item'].items():
                    if row['code'] == key:
                        old_quantity = session['cart_item'][key]['quantity']
                        total_quantity = old_quantity + _quantity
                        session['cart_item'][key]['quantity'] = total_quantity
                        session['cart_item'][key]['total_price'] = total_quantity * row['price']
            else:
                session['cart_item'] = array_merge(session['cart_item'], itemArray)
         
            for key, value in session['cart_item'].items():
                individual_quantity = int(session['cart_item'][key]['quantity'])
                individual_price = float(session['cart_item'][key]['total_price'])
                all_total_quantity = all_total_quantity + individual_quantity
                all_total_price = all_total_price + individual_price
        else:
            session['cart_item'] = itemArray
            all_total_quantity = all_total_quantity + _quantity
            all_total_price = all_total_price + _quantity * row['price']
             
        session['all_total_quantity'] = all_total_quantity
        session['all_total_price'] = all_total_price
                 
        return redirect(url_for('products'))
    else:
        return 'Error while adding item to cart'
 
@app.route('/empty')
def empty_cart():
    try:
        session.clear()
        return redirect(url_for('.products'))
    except Exception as e:
        print(e)
        flash('Order Placed successfully')
        return redirect(url_for('products'))
 
@app.route('/delete/<string:code>')
def delete_product(code):
    try:
        all_total_price = 0
        all_total_quantity = 0
        session.modified = True
         
        for item in session['cart_item'].items():
            if item[0] == code:    
                session['cart_item'].pop(item[0], None)
                if 'cart_item' in session:
                    for key, value in session['cart_item'].items():
                        individual_quantity = int(session['cart_item'][key]['quantity'])
                        individual_price = float(session['cart_item'][key]['total_price'])
                        all_total_quantity = all_total_quantity + individual_quantity
                        all_total_price = all_total_price + individual_price
                break
         
        if all_total_quantity == 0:
            session.clear()
        else:
            session['all_total_quantity'] = all_total_quantity
            session['all_total_price'] = all_total_price
             
        return redirect(url_for('.products'))
    except Exception as e:
        print(e)
 
def array_merge( first_array , second_array ):
    if isinstance( first_array , list ) and isinstance( second_array , list ):
        return first_array + second_array
    elif isinstance( first_array , dict ) and isinstance( second_array , dict ):
        return dict( list( first_array.items() ) + list( second_array.items() ) )
    elif isinstance( first_array , set ) and isinstance( second_array , set ):
        return first_array.union( second_array )
    return False





@app.route('/')
def Index():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    s = "SELECT * FROM product"
    cur.execute(s) # Execute the SQL
    list_products = cur.fetchall()
    return render_template('form.html', list_products = list_products)


@app.route('/add_product', methods=['POST'])
def add_product():
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST':
        fname = request.form['fname']
        email = request.form['email']
        zipcode = request.form['zipcode']
        city = request.form['city']
        address = request.form['address']
        cur.execute("INSERT INTO product (fname, email, zipcode city, address) VALUES (%s,%s,%s,%s,%s)", (fname, email,zipcode ,city, address))
        conn.commit()
        flash('Order Placed successfully')
        return redirect(url_for('products'))  
    
 
@app.route('/edit/<id>', methods = ['POST'])
def get_employee(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute('SELECT * FROM product WHERE id = %s',(id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('edit.html', product = data[0])
 
@app.route('/update/<id>', methods=['POST','GET'])
def update_product(id):
    if request.method == 'POST':
        fname = request.form['fname']
        email = request.form['email']
        zipcode = request.form['zipcode']
        city = request.form['city']
        address = request.form['address']
         
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("""""
            UPDATE product
            SET fname = %s,
                email = %s,
                zipcode = %s,
                city= %s,
                address= %s
            WHERE id = %s
        """"", (fname, email, zipcode, city, address, id))
        flash('Product Updated Successfully')
        conn.commit()
        return redirect(url_for('form')) 
 
@app.route('/delete/<string:id>', methods = ['POST','GET'])
def delete_products(id):
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    cur.execute('DELETE FROM product WHERE id = {0}'.format(id))
    conn.commit()
    flash('Order Cancelled')
    return redirect(url_for('form'))







@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        session.pop('user',None)
 
        if request.form['password'] == 'password':
            session['user'] = request.form['username']
            return redirect(url_for('login'))
    
    return render_template('products.html')
 
@app.route('/products')
def index():
    if g.user:
        return render_template('Products.html',user=session['user'])
    return redirect(url_for('products'))
 
@app.before_request
def before_request():
    g.user = None
 
    if 'user' in session:
        g.user = session['user']


 
@app.route('/dropsession')
def dropsession():
    session.pop('user',None)
    return render_template('login.html')


@app.route('/form')
def form():
    session.pop('user',None)
    return render_template('form.html')
 
 

if __name__ == "__main__":
 app.run(debug=True)