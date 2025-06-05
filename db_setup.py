import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from werkzeug.security import generate_password_hash

# Database connection settings
DB_USER = "postgres"  # Change to your PostgreSQL username
DB_PASSWORD = "Admin"  # Change to your PostgreSQL password
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "rental_db"

# Create the connection string
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create the SQLAlchemy engine
try:
    engine = create_engine(DATABASE_URL)
    print(f"Successfully connected to PostgreSQL database: {DB_NAME}")
except Exception as e:
    print(f"Error connecting to PostgreSQL database: {e}")
    sys.exit(1)

# Create a base class for declarative models
Base = declarative_base()

# Define models
class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False)
    bookings = relationship('Booking', backref='user', lazy=True)

class Vehicle(Base):
    __tablename__ = 'vehicle'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # car or bike
    model = Column(String(100), nullable=False)
    year = Column(Integer, nullable=False)
    price_per_day = Column(Float, nullable=False)
    image_url = Column(String(200), nullable=False)
    is_available = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    bookings = relationship('Booking', backref='vehicle', lazy=True)

class Booking(Base):
    __tablename__ = 'booking'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    vehicle_id = Column(Integer, ForeignKey('vehicle.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

def create_tables():
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        print("All tables created successfully!")
        return True
    except Exception as e:
        print(f"Error creating tables: {e}")
        return False

def insert_sample_data():
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add sample users
        admin_user = User(
            name="Admin User",
            email="admin@example.com",
            password=generate_password_hash("admin123"),
            is_admin=True
        )
        
        regular_user = User(
            name="John Doe",
            email="john@example.com",
            password=generate_password_hash("password123"),
            is_admin=False
        )
        
        session.add_all([admin_user, regular_user])
        session.commit()
        print("Sample users added successfully!")
        
        # Add sample vehicles
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
        
        session.add_all(vehicles)
        session.commit()
        print("Sample vehicles added successfully!")
        
        # Add sample bookings
        today = datetime.now()
        booking1 = Booking(
            user_id=2,  # John Doe
            vehicle_id=1,  # Toyota Camry
            start_date=today + timedelta(days=1),
            end_date=today + timedelta(days=4),
            total_price=180.0,  # 3 days * $60
            status="confirmed"
        )
        
        booking2 = Booking(
            user_id=2,  # John Doe
            vehicle_id=3,  # Yamaha MT-07
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            total_price=80.0,  # 2 days * $40
            status="pending"
        )
        
        session.add_all([booking1, booking2])
        session.commit()
        print("Sample bookings added successfully!")
        
        return True
    except Exception as e:
        session.rollback()
        print(f"Error inserting sample data: {e}")
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("Starting database setup...")
    
    # Create tables
    if create_tables():
        # Insert sample data
        insert_sample_data()
        
    print("\nDatabase setup complete!")
    print("\nYou can now run your Flask application with:")
    print("python app.py")
    
    print("\nAdmin login credentials:")
    print("Email: admin@example.com")
    print("Password: admin123")
    
    print("\nUser login credentials:")
    print("Email: john@example.com")
    print("Password: password123")