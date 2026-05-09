import os
import sqlite3
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify, g
)

app = Flask(__name__)
app.secret_key = 'ecommerce_secret_key_2024'

DATABASE = os.path.join(os.path.dirname(__file__), 'database', 'store.db')

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL,
            description TEXT,
            price       REAL    NOT NULL,
            stock       INTEGER NOT NULL DEFAULT 0,
            image_url   TEXT
        );

        CREATE TABLE IF NOT EXISTS orders (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT    NOT NULL,
            email         TEXT    NOT NULL,
            address       TEXT    NOT NULL,
            phone         TEXT,
            total_price   REAL    NOT NULL,
            status        TEXT    NOT NULL DEFAULT 'Pending',
            order_date    TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id   INTEGER NOT NULL REFERENCES orders(id)   ON DELETE CASCADE,
            product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
            quantity   INTEGER NOT NULL DEFAULT 1
        );
    """)

    # Seed products if table is empty
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        products = [
            ("Premium Wireless Headphones",
             "Experience crystal-clear audio with our top-of-the-line wireless headphones. Featuring 30-hour battery life, active noise cancellation, and premium leather ear cushions for all-day comfort.",
             79.99, 50,
             "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&q=80"),
            ("Smart Fitness Watch",
             "Track your health and fitness goals with this advanced smartwatch. Heart rate monitor, GPS, sleep tracking, and 7-day battery life packed into a sleek design.",
             129.99, 35,
             "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80"),
            ("Minimalist Leather Wallet",
             "Crafted from genuine full-grain leather, this slim bifold wallet holds up to 8 cards and cash while keeping your pocket slim and stylish.",
             39.99, 80,
             "https://images.unsplash.com/photo-1627123424574-724758594e93?w=600&q=80"),
            ("Portable Bluetooth Speaker",
             "Rugged, waterproof (IPX7) speaker with 360° surround sound, 20-hour playtime, and a built-in power bank. Perfect for outdoor adventures.",
             59.99, 45,
             "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=600&q=80"),
            ("Mechanical Keyboard",
             "Tactile and precise typing with Cherry MX Blue switches. Full RGB backlighting, aluminum frame, and N-key rollover for gaming and productivity alike.",
             109.99, 25,
             "https://images.unsplash.com/photo-1541140532154-b024d705b90a?w=600&q=80"),
            ("Ceramic Coffee Mug Set",
             "Set of 4 hand-crafted ceramic mugs in earth tones. Microwave and dishwasher safe, 12 oz capacity. Elevate your morning ritual.",
             34.99, 60,
             "https://images.unsplash.com/photo-1514228742587-6b1558fcca3d?w=600&q=80"),
            ("Stainless Steel Water Bottle",
             "Double-wall vacuum insulated bottle keeps drinks cold for 24 hours or hot for 12. BPA-free, leak-proof lid, and fits standard cup holders.",
             27.99, 100,
             "https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=600&q=80"),
            ("Sunglasses – Polarized UV400",
             "Stylish oversized frame with polarized lenses offering 100% UV400 protection. Lightweight TR-90 frame and spring hinges for a comfortable fit.",
             49.99, 55,
             "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=600&q=80"),
        ]
        db.executemany(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (?,?,?,?,?)",
            products
        )
    db.commit()
    db.close()


# Initialize database on app startup
init_db()


# ---------------------------------------------------------------------------
# Context processor – cart count badge
# ---------------------------------------------------------------------------

@app.context_processor
def inject_cart_count():
    cart = session.get('cart', {})
    count = sum(item['qty'] for item in cart.values())
    return {'cart_count': count}


# ===========================================================================
# FRONT STAGE – Public Store
# ===========================================================================

@app.route('/')
def index():
    db = get_db()
    search = request.args.get('q', '').strip()
    if search:
        products = db.execute(
            "SELECT * FROM products WHERE name LIKE ? OR description LIKE ?",
            (f'%{search}%', f'%{search}%')
        ).fetchall()
    else:
        products = db.execute("SELECT * FROM products").fetchall()
    return render_template('index.html', products=products, search=search)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('index'))
    return render_template('product.html', product=product)


# ---------------------------------------------------------------------------
# Cart
# ---------------------------------------------------------------------------

@app.route('/cart')
def cart():
    db = get_db()
    cart_data = session.get('cart', {})
    items = []
    total = 0.0
    for pid, info in cart_data.items():
        product = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if product:
            subtotal = product['price'] * info['qty']
            total += subtotal
            items.append({'product': product, 'qty': info['qty'], 'subtotal': subtotal})
    return render_template('cart.html', items=items, total=total)


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    qty = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    pid = str(product_id)
    if pid in cart:
        cart[pid]['qty'] += qty
    else:
        cart[pid] = {'qty': qty}
    session['cart'] = cart
    flash('Item added to cart!', 'success')
    return redirect(request.referrer or url_for('index'))


@app.route('/update_cart', methods=['POST'])
def update_cart():
    cart = session.get('cart', {})
    for key in list(cart.keys()):
        qty = int(request.form.get(f'qty_{key}', 0))
        if qty <= 0:
            cart.pop(key)
        else:
            cart[key]['qty'] = qty
    session['cart'] = cart
    flash('Cart updated.', 'info')
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<string:pid>')
def remove_from_cart(pid):
    cart = session.get('cart', {})
    cart.pop(pid, None)
    session['cart'] = cart
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))


# ---------------------------------------------------------------------------
# Checkout
# ---------------------------------------------------------------------------

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart_data = session.get('cart', {})
    if not cart_data:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    db = get_db()

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        email   = request.form.get('email', '').strip()
        address = request.form.get('address', '').strip()
        phone   = request.form.get('phone', '').strip()

        if not (name and email and address):
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('checkout'))

        # Calculate total
        total = 0.0
        for pid, info in cart_data.items():
            p = db.execute("SELECT price FROM products WHERE id = ?", (pid,)).fetchone()
            if p:
                total += p['price'] * info['qty']

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur = db.execute(
            "INSERT INTO orders (customer_name, email, address, phone, total_price, status, order_date) VALUES (?,?,?,?,?,?,?)",
            (name, email, address, phone, total, 'Pending', now)
        )
        order_id = cur.lastrowid

        for pid, info in cart_data.items():
            db.execute(
                "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?,?,?)",
                (order_id, int(pid), info['qty'])
            )
            # Decrease stock
            db.execute(
                "UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?",
                (info['qty'], int(pid))
            )
        db.commit()
        session.pop('cart', None)
        flash('success', 'order_placed')
        return render_template('checkout.html', success=True, order_id=order_id)

    # GET – render form
    items = []
    total = 0.0
    for pid, info in cart_data.items():
        p = db.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
        if p:
            subtotal = p['price'] * info['qty']
            total += subtotal
            items.append({'product': p, 'qty': info['qty'], 'subtotal': subtotal})
    return render_template('checkout.html', success=False, items=items, total=total)


# ===========================================================================
# BACK STAGE – Admin Dashboard
# ===========================================================================

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'store123'


def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid credentials. Please try again.', 'danger')
    return render_template('admin_login.html')


@app.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('admin_login'))


# ---------------------------------------------------------------------------
# Admin Dashboard
# ---------------------------------------------------------------------------

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    orders = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()

    # Attach items to each order
    orders_with_items = []
    for order in orders:
        items = db.execute("""
            SELECT oi.quantity, p.name, p.price
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
        """, (order['id'],)).fetchall()
        orders_with_items.append({'order': order, 'order_items': items})

    stats = {
        'total_products': len(products),
        'total_orders': len(orders),
        'revenue': db.execute("SELECT COALESCE(SUM(total_price),0) FROM orders").fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM orders WHERE status='Pending'").fetchone()[0],
    }
    return render_template('admin_dashboard.html', products=products,
                           orders_with_items=orders_with_items, stats=stats)


# ---------------------------------------------------------------------------
# Admin – Product CRUD
# ---------------------------------------------------------------------------

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price       = float(request.form.get('price', 0))
        stock       = int(request.form.get('stock', 0))
        image_url   = request.form.get('image_url', '').strip()

        if not name or price <= 0:
            flash('Product name and a valid price are required.', 'danger')
            return redirect(url_for('admin_add_product'))

        db = get_db()
        db.execute(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (?,?,?,?,?)",
            (name, description, price, stock, image_url)
        )
        db.commit()
        flash(f'Product "{name}" added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_product_form.html', product=None, action='Add')


@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        flash('Product not found.', 'danger')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price       = float(request.form.get('price', 0))
        stock       = int(request.form.get('stock', 0))
        image_url   = request.form.get('image_url', '').strip()

        db.execute(
            "UPDATE products SET name=?, description=?, price=?, stock=?, image_url=? WHERE id=?",
            (name, description, price, stock, image_url, product_id)
        )
        db.commit()
        flash(f'Product "{name}" updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_product_form.html', product=product, action='Edit')


@app.route('/admin/product/delete/<int:product_id>', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    db = get_db()
    product = db.execute("SELECT name FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        flash(f'Product "{product["name"]}" deleted.', 'success')
    return redirect(url_for('admin_dashboard'))


# ---------------------------------------------------------------------------
# Admin – Order Status Update
# ---------------------------------------------------------------------------

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    status = request.form.get('status', 'Pending')
    if status not in ('Pending', 'Shipped', 'Delivered'):
        status = 'Pending'
    db = get_db()
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    db.commit()
    flash(f'Order #{order_id} status updated to {status}.', 'success')
    return redirect(url_for('admin_dashboard') + '#orders')


@app.route('/admin/order/delete/<int:order_id>', methods=['POST'])
@admin_required
def admin_delete_order(order_id):
    db = get_db()
    db.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    db.commit()
    flash(f'Order #{order_id} deleted.', 'info')
    return redirect(url_for('admin_dashboard') + '#orders')


# ===========================================================================
# Entry point
# ===========================================================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)

# For Elastic Beanstalk
application = app
