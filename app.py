from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime, timedelta
import schedule # type: ignore
import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
CORS(app)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Email configuration
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"

# Models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    expiration_date = db.Column(db.Date, nullable=False)
    reminder_frequency = db.Column(db.Integer, nullable=False)
    minimum_stock = db.Column(db.Integer, nullable=False)
    last_reminder = db.Column(db.Date, nullable=True)

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    message = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    sent = db.Column(db.Boolean, default=False)

# Create tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'quantity': p.quantity,
        'expiration_date': p.expiration_date.isoformat(),
        'reminder_frequency': p.reminder_frequency,
        'minimum_stock': p.minimum_stock
    } for p in Product.query.all()])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    product = Product(
        name=data['name'],
        quantity=data['quantity'],
        expiration_date=datetime.strptime(data['expiration_date'], '%Y-%m-%d').date(),
        reminder_frequency=data['reminder_frequency'],
        minimum_stock=data['minimum_stock']
    )
    db.session.add(product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully'})

@app.route('/api/products/<int:product_id>/quantity', methods=['PATCH'])
def update_quantity(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    product.quantity += data['change']
    if product.quantity < 0:
        product.quantity = 0
    db.session.commit()
    return jsonify({'message': 'Quantity updated successfully'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/api/reminders', methods=['GET'])
def get_reminders():
    reminders = Reminder.query.filter_by(sent=False).all()
    return jsonify([{
        'id': r.id,
        'product_name': Product.query.get(r.product_id).name,
        'message': r.message,
        'due_date': r.due_date.isoformat()
    } for r in reminders])

@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    total_products = Product.query.count()
    low_stock = Product.query.filter(Product.quantity <= Product.minimum_stock).count()
    expiring_soon = Product.query.filter(
        Product.expiration_date <= (datetime.now() + timedelta(days=30)).date()
    ).count()
    
    return jsonify({
        'total_products': total_products,
        'low_stock': low_stock,
        'expiring_soon': expiring_soon
    })

def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def check_reminders():
    with app.app_context():
        today = datetime.now().date()
        
        # Check for low stock
        low_stock_products = Product.query.filter(Product.quantity <= Product.minimum_stock).all()
        for product in low_stock_products:
            message = f"Low stock alert: {product.name} (Quantity: {product.quantity})"
            reminder = Reminder(
                product_id=product.id,
                message=message,
                due_date=today
            )
            db.session.add(reminder)
            send_email(
                "Low Stock Alert",
                message,
                SMTP_USERNAME
            )
        
        # Check for expiring products
        expiring_products = Product.query.filter(
            Product.expiration_date <= (today + timedelta(days=30))
        ).all()
        for product in expiring_products:
            message = f"Expiration alert: {product.name} expires on {product.expiration_date}"
            reminder = Reminder(
                product_id=product.id,
                message=message,
                due_date=today
            )
            db.session.add(reminder)
            send_email(
                "Expiration Alert",
                message,
                SMTP_USERNAME
            )
        
        # Check consumption reminders
        products = Product.query.all()
        for product in products:
            if not product.last_reminder or \
               (today - product.last_reminder).days >= product.reminder_frequency:
                message = f"Consumption reminder: Time to take {product.name}"
                reminder = Reminder(
                    product_id=product.id,
                    message=message,
                    due_date=today
                )
                db.session.add(reminder)
                product.last_reminder = today
                send_email(
                    "Consumption Reminder",
                    message,
                    SMTP_USERNAME
                )
        
        db.session.commit()

def run_scheduler():
    schedule.every().day.at("09:00").do(check_reminders)
    while True:
        schedule.run_pending()
        time.sleep(60)

from flask import Flask, jsonify
from flask_cors import CORS  # type: ignore # Import CORS to avoid cross-origin issues

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

@app.route("/test-api", methods=["GET"])  # New API route
def test_api():
    return jsonify({"message": "Hello from Flask!"})  # Returns JSON response

if __name__ == "__main__":
    app.run(debug=True)
