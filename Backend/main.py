from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime
from passlib.context import CryptContext
from typing import List

from database import get_db, init_db
from pydantic import EmailStr
from models import (
    User, Role, Vehicle, Driver, Trip, MaintenanceLog, 
    FuelLog, Expense, RoleType, VehicleStatus, DriverStatus, TripStatus
)
from schemas import (
    LoginRequest, LoginResponse, UserResponse,
    VehicleCreate, VehicleUpdate, VehicleResponse,
    DriverCreate, DriverUpdate, DriverResponse,
    TripCreate, TripDispatch, TripComplete, TripResponse, TripListResponse,
    MaintenanceCreate, MaintenanceClose, MaintenanceResponse,
    FuelLogCreate, FuelLogResponse,
    ExpenseCreate, ExpenseResponse,
    DashboardKPI, VehicleAnalytics, AnalyticsResponse
)
from business_logic import (
    validate_and_create_trip, dispatch_trip, complete_trip, cancel_trip,
    create_maintenance_and_update_vehicle, close_maintenance,
    calculate_fuel_efficiency, calculate_operational_cost, calculate_vehicle_roi,
    get_dashboard_kpis, BusinessLogicException
)

# Initialize FastAPI app
app = FastAPI(
    title="TransitOps API",
    description="Smart Transport Operations Platform API",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============= STARTUP =============

@app.on_event("startup")
def startup():
    """Initialize database on startup"""
    init_db()

# ============= AUTH ENDPOINTS =============

@app.post("/api/auth/login", response_model=LoginResponse)
def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    """User login endpoint"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not pwd_context.verify(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User account is inactive")
    
    return LoginResponse(
        access_token=f"token_{user.id}_{user.email}",
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@app.post("/api/auth/register")
def register(
    email: EmailStr,
    password: str,
    full_name: str,
    role_type: RoleType = RoleType.DRIVER,
    db: Session = Depends(get_db)
):
    """User registration endpoint"""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Get or create role
    role = db.query(Role).filter(Role.type == role_type).first()
    if not role:
        role = Role(name=role_type.value, type=role_type)
        db.add(role)
        db.commit()
    
    # Create user
    user = User(
        email=email,
        password_hash=pwd_context.hash(password),
        full_name=full_name,
        role_id=role.id
    )
    db.add(user)
    db.commit()
    
    return {"message": "User registered successfully", "user_id": user.id}

# ============= VEHICLE ENDPOINTS =============

@app.post("/api/vehicles", response_model=VehicleResponse)
def create_vehicle(vehicle_data: VehicleCreate, db: Session = Depends(get_db)):
    """Create a new vehicle"""
    # Check if registration number already exists
    existing = db.query(Vehicle).filter(
        Vehicle.registration_number == vehicle_data.registration_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Vehicle with this registration number already exists"
        )
    
    vehicle = Vehicle(**vehicle_data.dict())
    db.add(vehicle)
    db.commit()
    db.refresh(vehicle)
    return vehicle

@app.get("/api/vehicles", response_model=List[VehicleResponse])
def list_vehicles(
    status: VehicleStatus = Query(None),
    vehicle_type: str = Query(None),
    db: Session = Depends(get_db)
):
    """List all vehicles with optional filters"""
    query = db.query(Vehicle)
    
    if status:
        query = query.filter(Vehicle.status == status)
    
    if vehicle_type:
        query = query.filter(Vehicle.vehicle_type == vehicle_type)
    
    return query.all()

@app.get("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    """Get vehicle by ID"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle

@app.put("/api/vehicles/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: int,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db)
):
    """Update vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    update_data = vehicle_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(vehicle, key, value)
    
    db.commit()
    db.refresh(vehicle)
    return vehicle

# ============= DRIVER ENDPOINTS =============

@app.post("/api/drivers", response_model=DriverResponse)
def create_driver(driver_data: DriverCreate, db: Session = Depends(get_db)):
    """Create a new driver"""
    # Check if license already exists
    existing = db.query(Driver).filter(
        Driver.license_number == driver_data.license_number
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Driver with this license number already exists"
        )
    
    driver = Driver(**driver_data.dict())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver

@app.get("/api/drivers", response_model=List[DriverResponse])
def list_drivers(
    status: DriverStatus = Query(None),
    db: Session = Depends(get_db)
):
    """List all drivers with optional filters"""
    query = db.query(Driver)
    
    if status:
        query = query.filter(Driver.status == status)
    
    return query.all()

@app.get("/api/drivers/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Get driver by ID"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    return driver

@app.put("/api/drivers/{driver_id}", response_model=DriverResponse)
def update_driver(
    driver_id: int,
    driver_data: DriverUpdate,
    db: Session = Depends(get_db)
):
    """Update driver"""
    driver = db.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    
    update_data = driver_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(driver, key, value)
    
    db.commit()
    db.refresh(driver)
    return driver

# ============= TRIP ENDPOINTS =============

@app.post("/api/trips", response_model=TripResponse)
def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    """Create a new trip"""
    from business_logic import generate_trip_number
    
    # Validate trip data
    vehicle, driver = validate_and_create_trip(
        trip_data.source_location,
        trip_data.destination_location,
        trip_data.vehicle_id,
        trip_data.driver_id,
        trip_data.cargo_weight,
        trip_data.planned_distance,
        db
    )
    
    trip = Trip(
        trip_number=generate_trip_number(),
        **trip_data.dict()
    )
    db.add(trip)
    db.commit()
    db.refresh(trip)
    
    return TripResponse.from_orm(trip)

@app.get("/api/trips", response_model=List[TripResponse])
def list_trips(
    status: TripStatus = Query(None),
    db: Session = Depends(get_db)
):
    """List all trips with optional filters"""
    query = db.query(Trip)
    
    if status:
        query = query.filter(Trip.status == status)
    
    return query.all()

@app.get("/api/trips/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: int, db: Session = Depends(get_db)):
    """Get trip by ID"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@app.post("/api/trips/{trip_id}/dispatch", response_model=TripResponse)
def dispatch_trip_endpoint(
    trip_id: int,
    dispatch_data: TripDispatch,
    db: Session = Depends(get_db)
):
    """Dispatch a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status != TripStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft trips can be dispatched")
    
    dispatch_trip(trip, dispatch_data.start_odometer, db)
    db.refresh(trip)
    return trip

@app.post("/api/trips/{trip_id}/complete", response_model=TripResponse)
def complete_trip_endpoint(
    trip_id: int,
    complete_data: TripComplete,
    db: Session = Depends(get_db)
):
    """Complete a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    if trip.status != TripStatus.DISPATCHED:
        raise HTTPException(status_code=400, detail="Only dispatched trips can be completed")
    
    complete_trip(trip, complete_data.end_odometer, complete_data.fuel_consumed, db)
    db.refresh(trip)
    return trip

@app.post("/api/trips/{trip_id}/cancel", response_model=TripResponse)
def cancel_trip_endpoint(trip_id: int, db: Session = Depends(get_db)):
    """Cancel a trip"""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    cancel_trip(trip, db)
    db.refresh(trip)
    return trip

# ============= MAINTENANCE ENDPOINTS =============

@app.post("/api/maintenance", response_model=MaintenanceResponse)
def create_maintenance(
    maintenance_data: MaintenanceCreate,
    db: Session = Depends(get_db)
):
    """Create a maintenance record"""
    maintenance = create_maintenance_and_update_vehicle(
        maintenance_data.vehicle_id,
        maintenance_data.maintenance_type,
        maintenance_data.description,
        maintenance_data.cost,
        maintenance_data.scheduled_date,
        db
    )
    return maintenance

@app.get("/api/maintenance", response_model=List[MaintenanceResponse])
def list_maintenance(vehicle_id: int = Query(None), db: Session = Depends(get_db)):
    """List maintenance records"""
    query = db.query(MaintenanceLog)
    
    if vehicle_id:
        query = query.filter(MaintenanceLog.vehicle_id == vehicle_id)
    
    return query.all()

@app.post("/api/maintenance/{maintenance_id}/close", response_model=MaintenanceResponse)
def close_maintenance_endpoint(
    maintenance_id: int,
    close_data: MaintenanceClose,
    db: Session = Depends(get_db)
):
    """Close a maintenance record"""
    close_maintenance(maintenance_id, close_data.completed_date, db)
    maintenance = db.query(MaintenanceLog).filter(MaintenanceLog.id == maintenance_id).first()
    return maintenance

# ============= FUEL LOG ENDPOINTS =============

@app.post("/api/fuel-logs", response_model=FuelLogResponse)
def create_fuel_log(fuel_data: FuelLogCreate, db: Session = Depends(get_db)):
    """Create a fuel log"""
    fuel_log = FuelLog(**fuel_data.dict())
    db.add(fuel_log)
    db.commit()
    db.refresh(fuel_log)
    return fuel_log

@app.get("/api/fuel-logs", response_model=List[FuelLogResponse])
def list_fuel_logs(vehicle_id: int = Query(None), db: Session = Depends(get_db)):
    """List fuel logs"""
    query = db.query(FuelLog)
    
    if vehicle_id:
        query = query.filter(FuelLog.vehicle_id == vehicle_id)
    
    return query.all()

# ============= EXPENSE ENDPOINTS =============

@app.post("/api/expenses", response_model=ExpenseResponse)
def create_expense(expense_data: ExpenseCreate, db: Session = Depends(get_db)):
    """Create an expense"""
    expense = Expense(**expense_data.dict())
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense

@app.get("/api/expenses", response_model=List[ExpenseResponse])
def list_expenses(vehicle_id: int = Query(None), db: Session = Depends(get_db)):
    """List expenses"""
    query = db.query(Expense)
    
    if vehicle_id:
        query = query.filter(Expense.vehicle_id == vehicle_id)
    
    return query.all()

# ============= DASHBOARD ENDPOINTS =============

@app.get("/api/dashboard/kpis", response_model=DashboardKPI)
def get_kpis(db: Session = Depends(get_db)):
    """Get dashboard KPIs"""
    return get_dashboard_kpis(db)

# ============= ANALYTICS ENDPOINTS =============

@app.get("/api/analytics/vehicles", response_model=AnalyticsResponse)
def get_vehicles_analytics(db: Session = Depends(get_db)):
    """Get analytics for all vehicles"""
    vehicles = db.query(Vehicle).all()
    
    vehicle_analytics_list = []
    for vehicle in vehicles:
        analytics = VehicleAnalytics(
            vehicle_id=vehicle.id,
            registration_number=vehicle.registration_number,
            vehicle_name=vehicle.vehicle_name,
            fuel_efficiency=calculate_fuel_efficiency(vehicle, db),
            fleet_utilization=0,  # Per-vehicle utilization would be complex
            operational_cost=calculate_operational_cost(vehicle, db),
            total_revenue=sum(
                trip.trip_cost or 0 for trip in db.query(Trip).filter(
                    Trip.vehicle_id == vehicle.id,
                    Trip.status == TripStatus.COMPLETED
                ).all()
            ),
            roi=calculate_vehicle_roi(vehicle, db)
        )
        vehicle_analytics_list.append(analytics)
    
    # Calculate total fleet utilization
    from business_logic import calculate_fleet_utilization
    total_utilization = calculate_fleet_utilization(db)
    
    total_cost = sum(va.operational_cost for va in vehicle_analytics_list)
    
    return AnalyticsResponse(
        vehicles=vehicle_analytics_list,
        total_fleet_utilization=total_utilization,
        total_operational_cost=total_cost
    )

@app.get("/api/analytics/vehicle/{vehicle_id}")
def get_vehicle_analytics(vehicle_id: int, db: Session = Depends(get_db)):
    """Get analytics for a specific vehicle"""
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    return VehicleAnalytics(
        vehicle_id=vehicle.id,
        registration_number=vehicle.registration_number,
        vehicle_name=vehicle.vehicle_name,
        fuel_efficiency=calculate_fuel_efficiency(vehicle, db),
        fleet_utilization=0,
        operational_cost=calculate_operational_cost(vehicle, db),
        total_revenue=sum(
            trip.trip_cost or 0 for trip in db.query(Trip).filter(
                Trip.vehicle_id == vehicle.id,
                Trip.status == TripStatus.COMPLETED
            ).all()
        ),
        roi=calculate_vehicle_roi(vehicle, db)
    )

# ============= HEALTH CHECK =============

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "TransitOps API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
