from database import SessionLocal, init_db
from models import Vehicle, VehicleStatus, User, Role, RoleType, Driver, DriverStatus, LicenseCategory, Trip, TripStatus
from passlib.context import CryptContext
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_db():
    init_db()  # Creates the tables
    db = SessionLocal()
    
    # 1. Seed the Admin User
    if db.query(User).count() == 0:
        print("Creating Admin Account...")
        role = db.query(Role).filter(Role.name == "fleet_manager").first()
        if not role:
            role = Role(name="fleet_manager", type=RoleType.FLEET_MANAGER)
            db.add(role)
            db.commit()
        
        admin = User(
            email="admin@transitops.com",
            password_hash=pwd_context.hash("admin123"),
            full_name="Om Sawant",
            role_id=role.id
        )
        db.add(admin)
        db.commit()
        print("Admin created: admin@transitops.com / admin123")

    # 2. Seed the Vehicles
    if db.query(Vehicle).count() == 0:
        print("Injecting initial fleet data...")
        fleet = [
            Vehicle(registration_number="TRK-001", vehicle_name="Heavy Hauler Alpha", vehicle_type="Truck", max_load_capacity=10000, acquisition_cost=150000, status=VehicleStatus.ON_TRIP),
            Vehicle(registration_number="VAN-082", vehicle_name="City Express B", vehicle_type="Van", max_load_capacity=2000, acquisition_cost=45000, status=VehicleStatus.AVAILABLE),
            Vehicle(registration_number="TRK-044", vehicle_name="Cargo Prime", vehicle_type="Truck", max_load_capacity=12000, acquisition_cost=180000, status=VehicleStatus.IN_SHOP),
        ]
        db.add_all(fleet)
        db.commit()
        print("Database seeded successfully!")
        
    # 3. Seed the Drivers
    if db.query(Driver).count() == 0:
        print("Injecting drivers data...")
        drivers_list = [
            Driver(name="Om Sawant", license_number="LIC-OM-999", license_category=LicenseCategory.HMV, license_expiry_date=datetime.utcnow() + timedelta(days=365*5), contact_number="+91 9999999999", safety_score=95.5, status=DriverStatus.AVAILABLE),
            Driver(name="Jane Doe", license_number="LIC-JD-123", license_category=LicenseCategory.LMV, license_expiry_date=datetime.utcnow() + timedelta(days=365*3), contact_number="+91 8888888888", safety_score=98.0, status=DriverStatus.AVAILABLE),
            Driver(name="John Smith", license_number="LIC-JS-456", license_category=LicenseCategory.PASSENGER, license_expiry_date=datetime.utcnow() + timedelta(days=365*2), contact_number="+91 7777777777", safety_score=89.0, status=DriverStatus.ON_TRIP)
        ]
        db.add_all(drivers_list)
        db.commit()
        print("Drivers seeded successfully!")

    # 4. Seed the Trips
    if db.query(Trip).count() == 0:
        print("Injecting initial trip data...")
        v1 = db.query(Vehicle).filter(Vehicle.registration_number == "TRK-001").first()
        d1 = db.query(Driver).filter(Driver.license_number == "LIC-JS-456").first()
        if v1 and d1:
            trip = Trip(
                trip_number="TRIP-A827B",
                source_location="Warehouse Alpha",
                destination_location="Distribution Center Beta",
                vehicle_id=v1.id,
                driver_id=d1.id,
                cargo_weight=5500.0,
                planned_distance=120.0,
                status=TripStatus.DISPATCHED,
                start_odometer=v1.current_odometer,
                dispatched_at=datetime.utcnow()
            )
            db.add(trip)
            db.commit()
            print("Trips seeded successfully!")

    db.close()

if __name__ == "__main__":
    seed_db()