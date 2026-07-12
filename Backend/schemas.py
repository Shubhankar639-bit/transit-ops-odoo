from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from models import RoleType, VehicleStatus, DriverStatus, TripStatus, LicenseCategory

# ============= AUTH SCHEMAS =============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: "RoleResponse"
    is_active: bool
    
    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str
    type: RoleType
    
    class Config:
        from_attributes = True

# ============= VEHICLE SCHEMAS =============

class VehicleCreate(BaseModel):
    registration_number: str
    vehicle_name: str
    vehicle_type: str
    max_load_capacity: float
    acquisition_cost: float

class VehicleUpdate(BaseModel):
    vehicle_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    max_load_capacity: Optional[float] = None
    acquisition_cost: Optional[float] = None
    status: Optional[VehicleStatus] = None

class VehicleResponse(BaseModel):
    id: int
    registration_number: str
    vehicle_name: str
    vehicle_type: str
    max_load_capacity: float
    current_odometer: float
    acquisition_cost: float
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============= DRIVER SCHEMAS =============

class DriverCreate(BaseModel):
    name: str
    license_number: str
    license_category: LicenseCategory
    license_expiry_date: datetime
    contact_number: str

class DriverUpdate(BaseModel):
    name: Optional[str] = None
    license_category: Optional[LicenseCategory] = None
    license_expiry_date: Optional[datetime] = None
    contact_number: Optional[str] = None
    safety_score: Optional[float] = None
    status: Optional[DriverStatus] = None

class DriverResponse(BaseModel):
    id: int
    name: str
    license_number: str
    license_category: LicenseCategory
    license_expiry_date: datetime
    contact_number: str
    safety_score: float
    status: DriverStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# ============= TRIP SCHEMAS =============

class TripCreate(BaseModel):
    source_location: str
    destination_location: str
    vehicle_id: int
    driver_id: int
    cargo_weight: float  # in kg
    planned_distance: float  # in km

class TripDispatch(BaseModel):
    start_odometer: float

class TripComplete(BaseModel):
    end_odometer: float
    fuel_consumed: float  # in liters

class TripResponse(BaseModel):
    id: int
    trip_number: str
    source_location: str
    destination_location: str
    vehicle_id: int
    driver_id: int
    cargo_weight: float
    planned_distance: float
    actual_distance: Optional[float]
    status: TripStatus
    start_odometer: Optional[float]
    end_odometer: Optional[float]
    fuel_consumed: Optional[float]
    trip_cost: Optional[float]
    created_at: datetime
    dispatched_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Include nested data
    vehicle: Optional[VehicleResponse] = None
    driver: Optional[DriverResponse] = None
    
    class Config:
        from_attributes = True

class TripListResponse(BaseModel):
    id: int
    trip_number: str
    source_location: str
    destination_location: str
    cargo_weight: float
    status: TripStatus
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= MAINTENANCE SCHEMAS =============

class MaintenanceCreate(BaseModel):
    vehicle_id: int
    maintenance_type: str
    description: Optional[str] = None
    cost: float
    scheduled_date: datetime

class MaintenanceClose(BaseModel):
    completed_date: datetime

class MaintenanceResponse(BaseModel):
    id: int
    vehicle_id: int
    maintenance_type: str
    description: Optional[str]
    cost: float
    scheduled_date: datetime
    completed_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============= FUEL LOG SCHEMAS =============

class FuelLogCreate(BaseModel):
    vehicle_id: int
    liters: float
    cost: float
    odometer_reading: Optional[float] = None

class FuelLogResponse(BaseModel):
    id: int
    vehicle_id: int
    liters: float
    cost: float
    date: datetime
    odometer_reading: Optional[float]
    
    class Config:
        from_attributes = True

# ============= EXPENSE SCHEMAS =============

class ExpenseCreate(BaseModel):
    vehicle_id: int
    expense_type: str  # toll, maintenance, cleaning, etc.
    amount: float
    description: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: int
    vehicle_id: int
    expense_type: str
    amount: float
    date: datetime
    description: Optional[str]
    
    class Config:
        from_attributes = True

# ============= DASHBOARD SCHEMAS =============

class DashboardKPI(BaseModel):
    active_vehicles: int
    available_vehicles: int
    vehicles_in_maintenance: int
    active_trips: int
    pending_trips: int
    drivers_on_duty: int
    fleet_utilization: float  # percentage

# ============= ANALYTICS SCHEMAS =============

class VehicleAnalytics(BaseModel):
    vehicle_id: int
    registration_number: str
    vehicle_name: str
    fuel_efficiency: float  # km/liter
    fleet_utilization: float  # percentage
    operational_cost: float
    total_revenue: float
    roi: float

class AnalyticsResponse(BaseModel):
    vehicles: List[VehicleAnalytics]
    total_fleet_utilization: float
    total_operational_cost: float
