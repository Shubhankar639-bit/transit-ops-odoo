from datetime import datetime
from sqlalchemy.orm import Session
from models import (
    Vehicle, Driver, Trip, MaintenanceLog, FuelLog, Expense,
    VehicleStatus, DriverStatus, TripStatus
)
from fastapi import HTTPException
import uuid

class BusinessLogicException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

# ============= VEHICLE LOGIC =============

def validate_vehicle_for_dispatch(vehicle: Vehicle, db: Session):
    """Validate if vehicle can be assigned to a trip"""
    if vehicle.status == VehicleStatus.RETIRED:
        raise BusinessLogicException(f"Vehicle {vehicle.registration_number} is retired")
    
    if vehicle.status == VehicleStatus.IN_SHOP:
        raise BusinessLogicException(f"Vehicle {vehicle.registration_number} is in maintenance")
    
    if vehicle.status == VehicleStatus.ON_TRIP:
        raise BusinessLogicException(f"Vehicle {vehicle.registration_number} is already on a trip")

def validate_vehicle_capacity(vehicle: Vehicle, cargo_weight: float):
    """Validate if cargo weight doesn't exceed vehicle capacity"""
    if cargo_weight > vehicle.max_load_capacity:
        raise BusinessLogicException(
            f"Cargo weight ({cargo_weight}kg) exceeds vehicle capacity ({vehicle.max_load_capacity}kg)"
        )

# ============= DRIVER LOGIC =============

def validate_driver_for_dispatch(driver: Driver):
    """Validate if driver can be assigned to a trip"""
    # Check if license is expired
    if driver.license_expiry_date < datetime.utcnow():
        raise BusinessLogicException(f"Driver {driver.name} has an expired license")
    
    if driver.status == DriverStatus.SUSPENDED:
        raise BusinessLogicException(f"Driver {driver.name} is suspended")
    
    if driver.status == DriverStatus.ON_TRIP:
        raise BusinessLogicException(f"Driver {driver.name} is already on a trip")

# ============= TRIP LOGIC =============

def generate_trip_number():
    """Generate unique trip number"""
    return f"TRIP-{uuid.uuid4().hex[:8].upper()}"

def validate_and_create_trip(
    source: str, 
    destination: str,
    vehicle_id: int,
    driver_id: int,
    cargo_weight: float,
    planned_distance: float,
    db: Session
):
    """Comprehensive validation for trip creation"""
    
    # Fetch vehicle
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise BusinessLogicException("Vehicle not found", 404)
    
    # Fetch driver
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise BusinessLogicException("Driver not found", 404)
    
    # Validate vehicle
    validate_vehicle_for_dispatch(vehicle, db)
    validate_vehicle_capacity(vehicle, cargo_weight)
    
    # Validate driver
    validate_driver_for_dispatch(driver)
    
    return vehicle, driver

def dispatch_trip(trip: Trip, start_odometer: float, db: Session):
    """Dispatch trip and update vehicle/driver status"""
    trip.status = TripStatus.DISPATCHED
    trip.start_odometer = start_odometer
    trip.dispatched_at = datetime.utcnow()
    
    # Update vehicle status
    trip.vehicle.status = VehicleStatus.ON_TRIP
    
    # Update driver status
    trip.driver.status = DriverStatus.ON_TRIP
    
    db.commit()

def complete_trip(trip: Trip, end_odometer: float, fuel_consumed: float, db: Session):
    """Complete trip and restore vehicle/driver status"""
    trip.status = TripStatus.COMPLETED
    trip.end_odometer = end_odometer
    trip.fuel_consumed = fuel_consumed
    trip.actual_distance = end_odometer - trip.start_odometer
    trip.completed_at = datetime.utcnow()
    
    # Update vehicle odometer
    trip.vehicle.current_odometer = end_odometer
    trip.vehicle.status = VehicleStatus.AVAILABLE
    
    # Update driver status
    trip.driver.status = DriverStatus.AVAILABLE
    
    # Calculate trip cost (fuel cost based on the actual fuel log)
    fuel_log = db.query(FuelLog).filter(
        FuelLog.vehicle_id == trip.vehicle_id
    ).order_by(FuelLog.id.desc()).first()
    
    if fuel_log:
        trip.trip_cost = fuel_log.cost
    
    db.commit()

def cancel_trip(trip: Trip, db: Session):
    """Cancel trip and restore vehicle/driver status"""
    if trip.status != TripStatus.DISPATCHED:
        raise BusinessLogicException("Only dispatched trips can be cancelled")
    
    trip.status = TripStatus.CANCELLED
    
    # Restore vehicle status
    trip.vehicle.status = VehicleStatus.AVAILABLE
    
    # Restore driver status
    trip.driver.status = DriverStatus.AVAILABLE
    
    db.commit()

# ============= MAINTENANCE LOGIC =============

def create_maintenance_and_update_vehicle(
    vehicle_id: int,
    maintenance_type: str,
    description: str,
    cost: float,
    scheduled_date: datetime,
    db: Session
):
    """Create maintenance record and automatically set vehicle to In Shop"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise BusinessLogicException("Vehicle not found", 404)
    
    # Cannot add maintenance if vehicle is on trip
    if vehicle.status == VehicleStatus.ON_TRIP:
        raise BusinessLogicException("Cannot add maintenance to vehicle currently on trip")
    
    # Create maintenance log
    maintenance = MaintenanceLog(
        vehicle_id=vehicle_id,
        maintenance_type=maintenance_type,
        description=description,
        cost=cost,
        scheduled_date=scheduled_date,
        is_active=True
    )
    
    # Automatically set vehicle status to In Shop
    vehicle.status = VehicleStatus.IN_SHOP
    
    db.add(maintenance)
    db.commit()
    return maintenance

def close_maintenance(maintenance_id: int, completed_date: datetime, db: Session):
    """Close maintenance and restore vehicle status"""
    maintenance = db.query(MaintenanceLog).filter(MaintenanceLog.id == maintenance_id).first()
    if not maintenance:
        raise BusinessLogicException("Maintenance record not found", 404)
    
    maintenance.completed_date = completed_date
    maintenance.is_active = False
    
    # Restore vehicle status to Available (unless it's retired)
    vehicle = maintenance.vehicle
    if vehicle.status != VehicleStatus.RETIRED:
        vehicle.status = VehicleStatus.AVAILABLE
    
    db.commit()

# ============= ANALYTICS LOGIC =============

def calculate_fuel_efficiency(vehicle: Vehicle, db: Session) -> float:
    """Calculate fuel efficiency (km/liter) for a vehicle"""
    trips = db.query(Trip).filter(
        Trip.vehicle_id == vehicle.id,
        Trip.status == TripStatus.COMPLETED
    ).all()
    
    if not trips:
        return 0.0
    
    total_distance = sum(trip.actual_distance or 0 for trip in trips)
    total_fuel = sum(trip.fuel_consumed or 0 for trip in trips)
    
    if total_fuel == 0:
        return 0.0
    
    return total_distance / total_fuel

def calculate_operational_cost(vehicle: Vehicle, db: Session) -> float:
    """Calculate total operational cost (fuel + maintenance) for a vehicle"""
    # Get all fuel logs for this vehicle
    fuel_logs = db.query(FuelLog).filter(FuelLog.vehicle_id == vehicle.id).all()
    total_fuel_cost = sum(log.cost for log in fuel_logs)
    
    # Get all maintenance costs
    maintenance_logs = db.query(MaintenanceLog).filter(MaintenanceLog.vehicle_id == vehicle.id).all()
    total_maintenance_cost = sum(log.cost for log in maintenance_logs)
    
    # Get all other expenses
    expenses = db.query(Expense).filter(Expense.vehicle_id == vehicle.id).all()
    total_expenses = sum(exp.amount for exp in expenses)
    
    return total_fuel_cost + total_maintenance_cost + total_expenses

def calculate_vehicle_roi(vehicle: Vehicle, db: Session) -> float:
    """Calculate ROI = (Revenue - (Maintenance + Fuel)) / Acquisition Cost"""
    # Revenue = sum of all trip costs
    trips = db.query(Trip).filter(
        Trip.vehicle_id == vehicle.id,
        Trip.status == TripStatus.COMPLETED
    ).all()
    
    total_revenue = sum(trip.trip_cost or 0 for trip in trips)
    operational_cost = calculate_operational_cost(vehicle, db)
    
    if vehicle.acquisition_cost == 0:
        return 0.0
    
    roi = (total_revenue - operational_cost) / vehicle.acquisition_cost
    return roi

def calculate_fleet_utilization(db: Session) -> float:
    """Calculate fleet utilization percentage"""
    total_vehicles = db.query(Vehicle).filter(Vehicle.status != VehicleStatus.RETIRED).count()
    on_trip_vehicles = db.query(Vehicle).filter(Vehicle.status == VehicleStatus.ON_TRIP).count()
    
    if total_vehicles == 0:
        return 0.0
    
    return (on_trip_vehicles / total_vehicles) * 100

def get_dashboard_kpis(db: Session):
    """Get all KPIs for dashboard"""
    from schemas import DashboardKPI
    
    active_vehicles = db.query(Vehicle).filter(
        Vehicle.status.in_([VehicleStatus.AVAILABLE, VehicleStatus.ON_TRIP])
    ).count()
    
    available_vehicles = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatus.AVAILABLE
    ).count()
    
    vehicles_in_maintenance = db.query(Vehicle).filter(
        Vehicle.status == VehicleStatus.IN_SHOP
    ).count()
    
    active_trips = db.query(Trip).filter(
        Trip.status == TripStatus.DISPATCHED
    ).count()
    
    pending_trips = db.query(Trip).filter(
        Trip.status == TripStatus.DRAFT
    ).count()
    
    drivers_on_duty = db.query(Driver).filter(
        Driver.status == DriverStatus.ON_TRIP
    ).count()
    
    fleet_utilization = calculate_fleet_utilization(db)
    
    return DashboardKPI(
        active_vehicles=active_vehicles,
        available_vehicles=available_vehicles,
        vehicles_in_maintenance=vehicles_in_maintenance,
        active_trips=active_trips,
        pending_trips=pending_trips,
        drivers_on_duty=drivers_on_duty,
        fleet_utilization=fleet_utilization
    )
