from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sys

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)

# PostgreSQL Connection Settings
DB_USER = "postgres"  # Default PostgreSQL username
DB_PASSWORD = "Admin"  # Replace with your actual PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "rental_db"

# Create the connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Vehicle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # car or bike
    model = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    price_per_day = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    bookings = db.relationship('Booking', backref='vehicle', lazy=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def home():
    vehicles = Vehicle.query.filter_by(is_available=True).limit(6).all()
    return render_template('index.html', vehicles=vehicles)

@app.route('/vehicles')
def vehicles():
    vehicle_type = request.args.get('type', 'all')
    if vehicle_type == 'all':
        vehicles = Vehicle.query.all()
    else:
        vehicles = Vehicle.query.filter_by(type=vehicle_type).all()
    return render_template('vehicles.html', vehicles=vehicles, type=vehicle_type)

@app.route('/vehicle/<int:id>')
def vehicle_detail(id):
    vehicle = Vehicle.query.get_or_404(id)
    return render_template('vehicle_detail.html', vehicle=vehicle)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already exists')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        new_user = User(name=name, email=email, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('register'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            flash('Login successful!')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash('You have been logged out')
    return redirect(url_for('home'))

@app.route('/admin/delete_user/<int:user_id>', methods=['GET', 'POST'])
def delete_user(user_id):
    # Check if user is logged in and is an admin
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    # Prevent admin from deleting their own account
    if user_id == session['user_id']:
        flash('You cannot delete your own account')
        return redirect(url_for('admin'))
    
    # Get the user to delete
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Delete all bookings associated with this user
            Booking.query.filter_by(user_id=user_id).delete()
            
            # Delete the user
            db.session.delete(user)
            db.session.commit()
            
            flash(f'User {user.name} has been deleted successfully')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error deleting the user: {str(e)}')
            return redirect(url_for('admin'))
    
    # GET request - show confirmation page
    return render_template('delete_user.html', user=user)

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login to view your dashboard')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    bookings = Booking.query.filter_by(user_id=session['user_id']).all()
    
    return render_template('dashboard.html', user=user, bookings=bookings)

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    vehicles = Vehicle.query.all()
    bookings = Booking.query.all()
    users = User.query.all()
    
    return render_template('admin.html', vehicles=vehicles, bookings=bookings, users=users)

@app.route('/book/<int:vehicle_id>', methods=['GET', 'POST'])
def book_vehicle(vehicle_id):
    if 'user_id' not in session:
        flash('Please login to book a vehicle')
        return redirect(url_for('login'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        
        # Calculate days difference
        days = (end_date - start_date).days
        if days < 1:
            flash('End date must be after start date')
            return redirect(url_for('book_vehicle', vehicle_id=vehicle_id))
        
        total_price = days * vehicle.price_per_day
        
        new_booking = Booking(
            user_id=session['user_id'],
            vehicle_id=vehicle_id,
            start_date=start_date,
            end_date=end_date,
            total_price=total_price,
            status='pending'
        )
        
        try:
            db.session.add(new_booking)
            vehicle.is_available = False
            db.session.commit()
            flash('Booking successful! Please wait for confirmation.')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('book_vehicle', vehicle_id=vehicle_id))
    
    return render_template('booking.html', vehicle=vehicle)

@app.route('/admin/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        name = request.form['name']
        vehicle_type = request.form['type']
        model = request.form['model']
        year = request.form['year']
        price_per_day = request.form['price_per_day']
        image_url = request.form['image_url']
        description = request.form['description']
        
        new_vehicle = Vehicle(
            name=name,
            type=vehicle_type,
            model=model,
            year=year,
            price_per_day=price_per_day,
            image_url=image_url,
            description=description,
            is_available=True
        )
        
        try:
            db.session.add(new_vehicle)
            db.session.commit()
            flash('Vehicle added successfully!')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('add_vehicle'))
    
    return render_template('add_vehicle.html')

@app.route('/admin/edit_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def edit_vehicle(vehicle_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        vehicle.name = request.form['name']
        vehicle.type = request.form['type']
        vehicle.model = request.form['model']
        vehicle.year = request.form['year']
        vehicle.price_per_day = request.form['price_per_day']
        vehicle.image_url = request.form['image_url']
        vehicle.is_available = True if request.form['is_available'] == 'True' else False
        vehicle.description = request.form['description']
        
        try:
            db.session.commit()
            flash('Vehicle updated successfully!')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('edit_vehicle', vehicle_id=vehicle_id))
    
    return render_template('edit_vehicle.html', vehicle=vehicle)

@app.route('/admin/delete_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def delete_vehicle(vehicle_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    
    if request.method == 'POST':
        try:
            # Delete associated bookings first to avoid foreign key constraint errors
            Booking.query.filter_by(vehicle_id=vehicle_id).delete()
            
            # Delete the vehicle
            db.session.delete(vehicle)
            db.session.commit()
            
            flash('Vehicle deleted successfully!')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('admin'))
    
    return render_template('delete_vehicle.html', vehicle=vehicle)

@app.route('/admin/update_booking/<int:booking_id>', methods=['POST'])
def update_booking(booking_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    booking = Booking.query.get_or_404(booking_id)
    status = request.form['status']
    
    booking.status = status
    if status == 'cancelled' or status == 'completed':
        booking.vehicle.is_available = True
    elif status == 'confirmed':
        booking.vehicle.is_available = False
    
    try:
        db.session.commit()
        flash('Booking updated successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an error: {str(e)}')
    
    # Check if we came from user details page
    referrer = request.referrer
    if referrer and 'view_user' in referrer:
        return redirect(url_for('view_user', user_id=booking.user_id))
    
    return redirect(url_for('admin'))

@app.route('/admin/update_booking/<int:booking_id>/<string:action>')
def admin_update_booking(booking_id, action):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    try:
        if action == 'approve':
            booking.status = 'confirmed'
            booking.vehicle.is_available = False
            flash('Booking approved successfully!')
        elif action == 'cancel':
            booking.status = 'cancelled'
            booking.vehicle.is_available = True
            flash('Booking cancelled successfully!')
        elif action == 'complete':
            booking.status = 'completed'
            booking.vehicle.is_available = True
            flash('Booking marked as completed!')
        else:
            flash('Invalid action')
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'There was an error: {str(e)}')
    
    # Check if we came from user details page
    referrer = request.referrer
    if referrer and 'view_user' in referrer:
        return redirect(url_for('view_user', user_id=booking.user_id))
    
    return redirect(url_for('admin'))

@app.route('/cancel_booking/<int:booking_id>', methods=['POST'])
def cancel_booking(booking_id):
    if 'user_id' not in session:
        flash('Please login to manage your bookings')
        return redirect(url_for('login'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Ensure the booking belongs to the current user
    if booking.user_id != session['user_id']:
        flash('Unauthorized access')
        return redirect(url_for('dashboard'))
    
    # Only allow cancellation of pending or confirmed bookings
    if booking.status not in ['pending', 'confirmed']:
        flash('This booking cannot be cancelled')
        return redirect(url_for('dashboard'))
    
    try:
        booking.status = 'cancelled'
        booking.vehicle.is_available = True
        db.session.commit()
        flash('Booking cancelled successfully!')
    except Exception as e:
        db.session.rollback()
        flash(f'There was an error: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('Please login to edit your profile')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        
        # Check if email is already taken by another user
        existing_user = User.query.filter(User.email == email, User.id != user.id).first()
        if existing_user:
            flash('Email already in use by another account')
            return redirect(url_for('edit_profile'))
        
        user.name = name
        user.email = email
        
        try:
            db.session.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('edit_profile'))
    
    return render_template('edit_profile.html', user=user)

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        flash('Please login to change your password')
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Verify current password
        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect')
            return redirect(url_for('change_password'))
        
        # Verify new password matches confirmation
        if new_password != confirm_password:
            flash('New passwords do not match')
            return redirect(url_for('change_password'))
        
        # Update password
        user.password = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash('Password changed successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('change_password'))
    
    return render_template('change_password.html', user=user)

@app.route('/admin/reset_password/<int:user_id>', methods=['GET', 'POST'])
def admin_reset_password(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        
        # Update password
        user.password = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            flash(f'Password for {user.name} reset successfully!')
            return redirect(url_for('admin'))
        except Exception as e:
            db.session.rollback()
            flash(f'There was an error: {str(e)}')
            return redirect(url_for('admin_reset_password', user_id=user_id))
    
    return render_template('admin_reset_password.html', user=user)

@app.route('/view_user/<int:user_id>')
def view_user(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    bookings = Booking.query.filter_by(user_id=user_id).all()
    
    # Count active and completed bookings
    active_bookings = sum(1 for b in bookings if b.status in ['pending', 'confirmed'])
    completed_bookings = sum(1 for b in bookings if b.status == 'completed')
    
    return render_template('view_user.html', 
                          user=user, 
                          bookings=bookings, 
                          active_bookings=active_bookings, 
                          completed_bookings=completed_bookings)

@app.route('/toggle_admin/<int:user_id>', methods=['POST'])
def toggle_admin(user_id):
    if 'user_id' not in session or not session.get('is_admin'):
        flash('Unauthorized access')
        return redirect(url_for('home'))
    
    user = User.query.get_or_404(user_id)
    
    # Don't allow changing the status of the current admin
    if user.id == session['user_id']:
        flash('You cannot change your own admin status')
        return redirect(url_for('view_user', user_id=user_id))
    
    # Toggle admin status
    user.is_admin = not user.is_admin
    
    try:
        db.session.commit()
        if user.is_admin:
            flash(f'{user.name} is now an admin')
        else:
            flash(f'{user.name} is no longer an admin')
        return redirect(url_for('view_user', user_id=user_id))
    except Exception as e:
        db.session.rollback()
        flash(f'There was an error: {str(e)}')
        return redirect(url_for('view_user', user_id=user_id))

# Function to create sample data
def create_sample_data():
    # Check if there are already users in the database
    if User.query.count() > 0:
        return
    
    # Create admin user
    admin = User(
        name="Admin User",
        email="admin@example.com",
        password=generate_password_hash("admin123"),
        is_admin=True
    )
    
    # Create regular user
    user = User(
        name="John Doe",
        email="user@example.com",
        password=generate_password_hash("user123"),
        is_admin=False
    )
    
    db.session.add_all([admin, user])
    
    # Create sample vehicles
    vehicles = [
        Vehicle(
            name="Toyota Camry",
            type="car",
            model="Camry SE",
            year=2022,
            price_per_day=60.0,
            image_url="https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?ixlib=rb-4.0.3",
            is_available=True,
            description="A comfortable sedan perfect for family trips. Features include GPS, Bluetooth, and backup camera."
        ),
        Vehicle(
            name="Honda Civic",
            type="car",
            model="Civic LX",
            year=2021,
            price_per_day=50.0,
            image_url="https://images.unsplash.com/photo-1606152421802-db97b9c7a11b?ixlib=rb-4.0.3",
            is_available=True,
            description="Fuel-efficient compact car with modern features. Includes Apple CarPlay, Android Auto, and lane assist."
        ),
        Vehicle(
            name="Yamaha MT-07",
            type="bike",
            model="MT-07",
            year=2023,
            price_per_day=40.0,
            image_url="https://images.unsplash.com/photo-1558981806-ec527fa84c39?ixlib=rb-4.0.3",
            is_available=True,
            description="Powerful middleweight motorcycle with excellent handling. Perfect for city rides and weekend trips."
        ),
        Vehicle(
            name="BMW R 1250 GS",
            type="bike",
            model="R 1250 GS Adventure",
            year=2022,
            price_per_day=80.0,
            image_url="https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?ixlib=rb-4.0.3",
            is_available=True,
            description="Premium adventure motorcycle for long-distance touring. Features include heated grips, cruise control, and multiple riding modes."
        ),
        Vehicle(
            name="Ford Mustang",
            type="car",
            model="Mustang GT",
            year=2023,
            price_per_day=90.0,
            image_url="https://images.unsplash.com/photo-1584345604476-8ec5e12e42dd?ixlib=rb-4.0.3",
            is_available=True,
            description="Iconic American muscle car with a powerful V8 engine. Includes premium sound system and leather seats."
        ),
        Vehicle(
            name="Ducati Panigale V4",
            type="bike",
            model="Panigale V4 S",
            year=2023,
            price_per_day=100.0,
            image_url="https://images.unsplash.com/photo-1568772585407-9361f9bf3a87?ixlib=rb-4.0.3",
            is_available=True,
            description="High-performance superbike with cutting-edge technology. Features include electronic suspension, quick shifter, and traction control."
        )
    ]
    
    db.session.add_all(vehicles)
    
    try:
        db.session.commit()
        print("Sample data created successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {str(e)}")

def test_db_connection():
    """Test the database connection and print the result."""
    try:
        with app.app_context():
            db.engine.connect()
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("\nPossible solutions:")
        print("1. Check if PostgreSQL is running")
        print("2. Verify your username and password")
        print("3. Make sure the database 'rental_db' exists")
        print("4. Check if PostgreSQL is listening on port 5432")
        return False

if __name__ == '__main__':
    # Test database connection before creating tables
    print("\n=== Testing PostgreSQL Connection ===")
    if test_db_connection():
        with app.app_context():
            try:
                print("\n=== Creating Database Tables ===")
                db.create_all()
                print("✅ Tables created successfully!")
                
                print("\n=== Creating Sample Data ===")
                create_sample_data()
                
                print("\n=== Starting Flask Application ===")
                print("Access the application at http://localhost:5000")
                print("\nLogin credentials:")
                print("Admin: admin@example.com / admin123")
                print("User: user@example.com / user123")
                
                app.run(debug=True)
            except Exception as e:
                print(f"❌ Error setting up application: {str(e)}")
    else:
        print("\n❌ Cannot start application due to database connection issues.")
        sys.exit(1)