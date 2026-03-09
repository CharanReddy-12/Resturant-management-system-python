from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'btech_restaurant_secret_2024'

DB_PATH = 'restaurant.db'

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    # ── Always delete old DB and recreate fresh ──
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️  Old database deleted.")

    conn = get_db()
    c = conn.cursor()

    # Menu table
    c.execute('''CREATE TABLE IF NOT EXISTS menu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        stock INTEGER NOT NULL DEFAULT 50,
        image_url TEXT DEFAULT ""
    )''')

    # Bills table
    c.execute('''CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        items TEXT NOT NULL,
        total REAL NOT NULL,
        payment_method TEXT NOT NULL,
        created_at TEXT NOT NULL
    )''')

    # Reservations table
    c.execute('''CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        table_no INTEGER NOT NULL,
        created_at TEXT NOT NULL
    )''')

    # ── Always seed 15 default menu items with images ──
    items = [
        ('Veg Biryani',          120, 40, 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400&q=80'),
        ('Chicken Biryani',      180, 35, 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400&q=80'),
        ('Paneer Butter Masala', 150, 30, 'https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400&q=80'),
        ('Dal Tadka',            100, 50, 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400&q=80'),
        ('Butter Naan',           40, 80, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&q=80'),
        ('Masala Dosa',           90, 45, 'https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=400&q=80'),
        ('Idli Sambar',           70, 60, 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400&q=80'),
        ('Veg Fried Rice',       110, 40, 'https://images.unsplash.com/photo-1603133872878-684f208fb84b?w=400&q=80'),
        ('Chicken Curry',        160, 25, 'https://images.unsplash.com/photo-1588166524941-3bf61a9c41db?w=400&q=80'),
        ('Mango Lassi',           60, 70, 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=400&q=80'),
        ('Cold Coffee',           80, 55, 'https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=400&q=80'),
        ('Gulab Jamun',           60, 60, 'https://images.unsplash.com/photo-1666195412511-f3a58d7b71b3?w=400&q=80'),
        ('Samosa',                30, 90, 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=400&q=80'),
        ('Chole Bhature',        130, 35, 'https://images.unsplash.com/photo-1626132647523-66c62e24cb3c?w=400&q=80'),
        ('Chicken Tandoori',     200, 20, 'https://images.unsplash.com/photo-1599487488170-d11ec9c172f0?w=400&q=80'),
    ]
    c.executemany("INSERT INTO menu (name, price, stock, image_url) VALUES (?, ?, ?, ?)", items)
    print(f"✅ Database created with {len(items)} menu items.")

    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')

# ─────────────────────────────────────────────
# USER MODULE
# ─────────────────────────────────────────────
@app.route('/user', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Please enter your name.', 'danger')
            return render_template('user_login.html')
        session['user_name'] = name
        return redirect(url_for('user_dashboard'))
    return render_template('user_login.html')

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_name' not in session:
        return redirect(url_for('user_login'))
    return render_template('user_dashboard.html', name=session['user_name'])

@app.route('/user/menu')
def user_menu():
    if 'user_name' not in session:
        return redirect(url_for('user_login'))
    conn = get_db()
    items = conn.execute("SELECT id, name, price, image_url FROM menu").fetchall()
    conn.close()
    return render_template('user_menu.html', items=items, name=session['user_name'])

@app.route('/user/order', methods=['GET', 'POST'])
def place_order():
    if 'user_name' not in session:
        return redirect(url_for('user_login'))
    conn = get_db()
    items = conn.execute("SELECT id, name, price, image_url FROM menu").fetchall()
    conn.close()

    if request.method == 'POST':
        selected_ids = request.form.getlist('item_id')
        quantities = request.form.getlist('quantity')

        if not selected_ids:
            flash('Please select at least one item.', 'danger')
            return render_template('order.html', items=items, name=session['user_name'])

        order_items = []
        total = 0
        conn = get_db()
        for item_id, qty in zip(selected_ids, quantities):
            try:
                qty = int(qty)
                if qty <= 0:
                    continue
            except:
                continue
            row = conn.execute("SELECT * FROM menu WHERE id=?", (item_id,)).fetchone()
            if row:
                subtotal = row['price'] * qty
                total += subtotal
                order_items.append({
                    'name': row['name'],
                    'price': row['price'],
                    'qty': qty,
                    'subtotal': subtotal
                })
        conn.close()

        if not order_items:
            flash('Please enter valid quantities.', 'danger')
            return render_template('order.html', items=items, name=session['user_name'])

        session['pending_order'] = order_items
        session['pending_total'] = total
        return redirect(url_for('payment'))

    return render_template('order.html', items=items, name=session['user_name'])

@app.route('/user/payment', methods=['GET', 'POST'])
def payment():
    if 'user_name' not in session or 'pending_order' not in session:
        return redirect(url_for('user_login'))

    if request.method == 'POST':
        method = request.form.get('payment_method')
        if method not in ['Cash', 'Card']:
            flash('Please select a payment method.', 'danger')
            return render_template('payment.html',
                                   order=session['pending_order'],
                                   total=session['pending_total'],
                                   name=session['user_name'])

        # Save bill
        conn = get_db()
        items_str = '; '.join([f"{i['name']} x{i['qty']} @₹{i['price']}" for i in session['pending_order']])
        conn.execute(
            "INSERT INTO bills (user_name, items, total, payment_method, created_at) VALUES (?,?,?,?,?)",
            (session['user_name'], items_str, session['pending_total'], method, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        bill_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()

        # Copy all data BEFORE clearing the session
        ordered_items = [dict(i) for i in session['pending_order']]
        ordered_total = float(session['pending_total'])
        customer_name = str(session['user_name'])
        session.pop('pending_order', None)
        session.pop('pending_total', None)

        bill_data = {
            'id': int(bill_id),
            'user_name': customer_name,
            'order_items': ordered_items,
            'total': ordered_total,
            'payment_method': str(method),
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return render_template('bill.html', bill=bill_data)

    return render_template('payment.html',
                           order=session['pending_order'],
                           total=session['pending_total'],
                           name=session['user_name'])

@app.route('/user/book', methods=['GET', 'POST'])
def book_table():
    if 'user_name' not in session:
        return redirect(url_for('user_login'))

    conn = get_db()
    booked = [r['table_no'] for r in conn.execute("SELECT table_no FROM reservations").fetchall()]
    conn.close()

    if request.method == 'POST':
        try:
            table_no = int(request.form.get('table_no'))
        except:
            flash('Invalid table number.', 'danger')
            return render_template('book_table.html', booked=booked, name=session['user_name'])

        if table_no < 1 or table_no > 20:
            flash('Please select a table between 1 and 20.', 'danger')
            return render_template('book_table.html', booked=booked, name=session['user_name'])

        if table_no in booked:
            flash(f'Table {table_no} is already booked. Please choose another.', 'danger')
            return render_template('book_table.html', booked=booked, name=session['user_name'])

        conn = get_db()
        conn.execute(
            "INSERT INTO reservations (user_name, table_no, created_at) VALUES (?,?,?)",
            (session['user_name'], table_no, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        conn.commit()
        conn.close()
        flash(f'🎉 Table {table_no} booked successfully for {session["user_name"]}!', 'success')
        return redirect(url_for('book_table'))

    return render_template('book_table.html', booked=booked, name=session['user_name'])

@app.route('/user/logout')
def user_logout():
    session.pop('user_name', None)
    return redirect(url_for('home'))

# ─────────────────────────────────────────────
# ADMIN MODULE
# ─────────────────────────────────────────────
ADMIN_PASSWORD = '1234'

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():#Admin Login
    if request.method == 'POST':
        pwd = request.form.get('password', '')
        if pwd == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Incorrect password. Try again.', 'danger')
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():#Admin Dashboard
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin_dashboard.html')

@app.route('/admin/menu')
def admin_menu():#Admin menu
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    items = conn.execute("SELECT id, name, price, stock, image_url FROM menu").fetchall()
    conn.close()
    return render_template('admin_menu.html', items=items)

@app.route('/admin/add', methods=['GET', 'POST'])
def add_item():#Add item
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        price = request.form.get('price', '')
        stock = request.form.get('stock', '')
        if not name or not price or not stock:
            flash('All fields are required.', 'danger')
            return render_template('add_item.html')
        try:
            price = float(price)
            stock = int(stock)
        except:
            flash('Price and stock must be numbers.', 'danger')
            return render_template('add_item.html')
        conn = get_db()
        conn.execute("INSERT INTO menu (name, price, stock) VALUES (?,?,?)", (name, price, stock))
        conn.commit()
        conn.close()
        flash(f'✅ Item "{name}" added successfully!', 'success')
        return redirect(url_for('admin_menu'))
    return render_template('add_item.html')

@app.route('/admin/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):#Delete Item
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    item = conn.execute("SELECT name FROM menu WHERE id=?", (item_id,)).fetchone()
    if item:
        conn.execute("DELETE FROM menu WHERE id=?", (item_id,))
        conn.commit()
        flash(f'🗑️ Item "{item["name"]}" deleted.', 'success')
    conn.close()
    return redirect(url_for('admin_menu'))

@app.route('/admin/bills')
def admin_bills():#Admin bills
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    bills = conn.execute("SELECT * FROM bills ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin_bills.html', bills=bills)

@app.route('/admin/reservations')
def admin_reservations():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    conn = get_db()
    reservations = conn.execute("SELECT * FROM reservations ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('admin_reservations.html', reservations=reservations)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route('/quit')
def quit_app():
    return render_template('quit.html')

if __name__ == '__main__':
    init_db()   # Deletes.
    app.run(debug=True, host='0.0.0.0', port=5000)