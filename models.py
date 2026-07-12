from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database import Base

# ============= ENUMS =============
class RoleType(str, enum.Enum):
    FLEET_MANAGER = "fleet_manager"
    DRIVER = "driver"
    SAFETY_OFFICER = "safety_officer"
    FINANCIAL_ANALYST = "financial_analyst"

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    IN_SHOP = "in_shop"
    RETIRED = "retired"

class DriverStatus(str, enum.Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    OFF_DUTY = "off_duty"
    SUSPENDED = "suspended"

class TripStatus(str, enum.Enum):
    DRAFT = "draft"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class LicenseCategory(str, enum.Enum):
    LMV = "lmv"  # Light Motor Vehicle
    HMV = "hmv"  # Heavy Motor Vehicle
    PASSENGER = "passenger"

# ============= MODELS =============

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    type = Column(Enum(RoleType), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")

class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = Column(Integer, primary_key=True)
    registration_number = Column(String(20), unique=True, nullable=False, index=True)
    vehicle_name = Column(String(100), nullable=False)
    vehicle_type = Column(String(50), nullable=False)  # e.g., Van, Truck, Bike
    max_load_capacity = Column(Float, nullable=False)  # in kg
    current_odometer = Column(Float, default=0)  # in km
    acquisition_cost = Column(Float, nullable=False)
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trips = relationship("Trip", back_populates="vehicle")
    maintenance_logs = relationship("MaintenanceLog", back_populates="vehicle")
    fuel_logs = relationship("FuelLog", back_populates="vehicle")
    expenses = relationship("Expense", back_populates="vehicle")

class Driver(Base):
    __tablename__ = "drivers"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    license_number = Column(String(50), unique=True, nullable=False, index=True)
    license_category = Column(Enum(LicenseCategory), nullable=False)
    license_expiry_date = Column(DateTime, nullable=False)
    contact_number = Column(String(20), nullable=False)
    safety_score = Column(Float, default=100)  # Out of 100
    status = Column(Enum(DriverStatus), default=DriverStatus.AVAILABLE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    trips = relationship("Trip", back_populates="driver")

class Trip(Base):
    __tablename__ = "trips"
    
    id = Column(Integer, primary_key=True)
    trip_number = Column(String(50), unique=True, nullable=False, index=True)
    source_location = Column(String(200), nullable=False)
    destination_location = Column(String(200), nullable=False)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    cargo_weight = Column(Float, nullable=False)  # in kg
    planned_distance = Column(Float, nullable=False)  # in km
    actual_distance = Column(Float, nullable=True)  # in km
    status = Column(Enum(TripStatus), default=TripStatus.DRAFT)
    start_odometer = Column(Float, nullable=True)
    end_odometer = Column(Float, nullable=True)
    fuel_consumed = Column(Float, nullable=True)  # in liters
    trip_cost = Column(Float, nullable=True)  # Total cost for this trip
    created_at = Column(DateTime, default=datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("Driver", back_populates="trips")

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    maintenance_type = Column(String(100), nullable=False)  # e.g., Oil Change, Tire Replacement
    description = Column(String(500), nullable=True)
    cost = Column(Float, nullable=False)
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)  # True if vehicle is currently in shop
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="maintenance_logs")

class FuelLog(Base):
    __tablename__ = "fuel_logs"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    liters = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    odometer_reading = Column(Float, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="fuel_logs")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)
    expense_type = Column(String(50), nullable=False)  # e.g., toll, maintenance, cleaning
    amount = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    description = Column(String(200), nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="expenses")
