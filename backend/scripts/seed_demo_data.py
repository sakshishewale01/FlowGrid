"""
FlowGrid - Demo Data Seeder
===========================
Populates realistic demo records in the development PostgreSQL database:
- Warehouses (Chicago, Newark, Dallas)
- Products (commercial items/SKUs)
- Inventories (stocks and reorder thresholds)
- Drivers (linked to driver user accounts)
- Vehicles (transport units with capacities)
- Shipments (across various lifecycle stages)
- Routes (freight corridors)
"""

from decimal import Decimal
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.warehouse import Warehouse
from app.models.product import Product
from app.models.inventory import Inventory
from app.models.driver import Driver
from app.models.vehicle import Vehicle
from app.models.shipment import Shipment, ShipmentStatus
from app.models.route import Route
from app.core.security import get_password_hash


def seed_demo_data():
    db = SessionLocal()
    try:
        # 1. Warehouses
        if db.query(Warehouse).count() == 0:
            wh_chicago = Warehouse(
                name="Midwest Regional Hub (ORD-01)",
                location="Chicago, IL",
                address="1000 Logistics Blvd, Chicago, IL 60666",
                capacity=250000,
                is_active=True,
            )
            wh_newark = Warehouse(
                name="East Coast Gateway (EWR-02)",
                location="Newark, NJ",
                address="250 Freight Way, Newark, NJ 07114",
                capacity=310000,
                is_active=True,
            )
            wh_dallas = Warehouse(
                name="Southwest Logistics Center (DFW-04)",
                location="Dallas, TX",
                address="500 Cargo Parkway, Dallas, TX 75261",
                capacity=180000,
                is_active=True,
            )
            db.add_all([wh_chicago, wh_newark, wh_dallas])
            db.commit()
            print("Seeded 3 Warehouses.")
        else:
            wh_chicago = db.query(Warehouse).filter(Warehouse.location.like("%Chicago%")).first()
            wh_newark = db.query(Warehouse).filter(Warehouse.location.like("%Newark%")).first()
            wh_dallas = db.query(Warehouse).filter(Warehouse.location.like("%Dallas%")).first()

        # 2. Products
        if db.query(Product).count() == 0:
            p1 = Product(
                name="Enterprise Core Switch",
                sku="SKU-ELEC-402",
                description="High-density rackmount multi-gigabit routing switch",
                unit_price=Decimal("1250.00"),
                is_active=True,
            )
            p2 = Product(
                name="IoT Telematics Sensor Array",
                sku="SKU-SENS-109",
                description="Cellular and GPS multi-axis telemetry monitor",
                unit_price=Decimal("185.50"),
                is_active=True,
            )
            p3 = Product(
                name="Lithium Fleet Battery Pack",
                sku="SKU-BAT-880",
                description="48V 100Ah heavy-duty warehouse tugger battery module",
                unit_price=Decimal("450.00"),
                is_active=True,
            )
            p4 = Product(
                name="Monocrystalline Solar Unit",
                sku="SKU-SOL-312",
                description="400W commercial rooftop PV generation panel",
                unit_price=Decimal("680.00"),
                is_active=True,
            )
            p5 = Product(
                name="Industrial Armored Fiber Cable",
                sku="SKU-CAB-050",
                description="100m spool of tactical armored 24-core SMF optical line",
                unit_price=Decimal("75.00"),
                is_active=True,
            )
            db.add_all([p1, p2, p3, p4, p5])
            db.commit()
            print("Seeded 5 Products.")
        else:
            p1 = db.query(Product).first()

        # 3. Inventory Stock
        if db.query(Inventory).count() == 0 and wh_chicago:
            products = db.query(Product).all()
            inv_records = [
                Inventory(warehouse_id=wh_chicago.id, product_id=products[0].id, quantity=450, reorder_level=50),
                Inventory(warehouse_id=wh_chicago.id, product_id=products[1].id, quantity=30, reorder_level=40),  # Low stock
                Inventory(warehouse_id=wh_newark.id, product_id=products[2].id, quantity=800, reorder_level=100),
                Inventory(warehouse_id=wh_newark.id, product_id=products[3].id, quantity=120, reorder_level=30),
                Inventory(warehouse_id=wh_dallas.id, product_id=products[4].id, quantity=650, reorder_level=80),
            ]
            db.add_all(inv_records)
            db.commit()
            print("Seeded 5 Inventory stock records.")

        # 4. Driver Users & Driver Profiles
        driver_user = db.query(User).filter(User.email == "driver@flowgrid.io").first()
        if not driver_user:
            driver_user = User(
                name="Alex Rivera",
                email="driver@flowgrid.io",
                hashed_password=get_password_hash("DriverPass123!"),
                role=UserRole.DRIVER,
                is_active=True,
            )
            db.add(driver_user)
            db.commit()
            db.refresh(driver_user)

        driver_rec = db.query(Driver).filter(Driver.user_id == driver_user.id).first()
        if not driver_rec:
            driver_rec = Driver(
                user_id=driver_user.id,
                license_number="CDL-IL-984210",
                phone_number="+1-312-555-0199",
                availability_status="IN_TRANSIT",
            )
            db.add(driver_rec)
            db.commit()
            db.refresh(driver_rec)
            print("Seeded Driver Profile for Alex Rivera.")

        # 5. Vehicles
        if db.query(Vehicle).count() == 0:
            v1 = Vehicle(
                registration_number="UNIT-402",
                vehicle_type="Semi-Trailer",
                capacity=Decimal("20000.00"),
                status="IN_USE",
            )
            v2 = Vehicle(
                registration_number="UNIT-118",
                vehicle_type="Box Truck",
                capacity=Decimal("8000.00"),
                status="IN_USE",
            )
            v3 = Vehicle(
                registration_number="UNIT-305",
                vehicle_type="Flatbed",
                capacity=Decimal("15000.00"),
                status="AVAILABLE",
            )
            db.add_all([v1, v2, v3])
            db.commit()
            print("Seeded 3 Fleet Vehicles.")
        else:
            v1 = db.query(Vehicle).first()

        # 6. Shipments
        if db.query(Shipment).count() == 0 and wh_chicago:
            v1 = db.query(Vehicle).first()
            s1 = Shipment(
                tracking_number="FG-98421-US",
                origin_warehouse_id=wh_chicago.id,
                destination_address="420 Industrial Drive",
                destination_city="Detroit",
                destination_state="MI",
                destination_postal_code="48201",
                assigned_driver_id=driver_rec.id if driver_rec else None,
                assigned_vehicle_id=v1.id if v1 else None,
                status=ShipmentStatus.IN_TRANSIT,
                total_weight_kg=Decimal("4250.00"),
                total_volume_cbm=Decimal("18.40"),
            )
            s2 = Shipment(
                tracking_number="FG-98422-US",
                origin_warehouse_id=wh_newark.id,
                destination_address="88 Metro Harbor Rd",
                destination_city="Boston",
                destination_state="MA",
                destination_postal_code="02108",
                status=ShipmentStatus.IN_TRANSIT,
                total_weight_kg=Decimal("1120.00"),
                total_volume_cbm=Decimal("5.20"),
            )
            s3 = Shipment(
                tracking_number="FG-98423-US",
                origin_warehouse_id=wh_dallas.id,
                destination_address="1400 Lone Star Way",
                destination_city="Austin",
                destination_state="TX",
                destination_postal_code="73301",
                status=ShipmentStatus.DELIVERED,
                delivered_at=datetime.now(timezone.utc),
                total_weight_kg=Decimal("7800.00"),
                total_volume_cbm=Decimal("24.00"),
            )
            s4 = Shipment(
                tracking_number="FG-98424-US",
                origin_warehouse_id=wh_chicago.id,
                destination_address="700 Freight Terminal",
                destination_city="Minneapolis",
                destination_state="MN",
                destination_postal_code="55401",
                status=ShipmentStatus.FAILED,
                total_weight_kg=Decimal("3400.00"),
                total_volume_cbm=Decimal("12.00"),
            )
            s5 = Shipment(
                tracking_number="FG-98425-US",
                origin_warehouse_id=wh_newark.id,
                destination_address="12 Crossdock Circle",
                destination_city="Philadelphia",
                destination_state="PA",
                destination_postal_code="19104",
                status=ShipmentStatus.ASSIGNED,
                total_weight_kg=Decimal("1850.00"),
                total_volume_cbm=Decimal("8.50"),
            )
            s6 = Shipment(
                tracking_number="FG-98426-US",
                origin_warehouse_id=wh_chicago.id,
                destination_address="200 Lakeview St",
                destination_city="Cleveland",
                destination_state="OH",
                destination_postal_code="44101",
                status=ShipmentStatus.CONFIRMED,
                total_weight_kg=Decimal("2200.00"),
                total_volume_cbm=Decimal("9.10"),
            )
            db.add_all([s1, s2, s3, s4, s5, s6])
            db.commit()
            print("Seeded 6 Shipments.")

        # 7. Routes / Corridors
        if db.query(Route).count() == 0:
            r1 = Route(
                name="I-80 Corridor: Chicago → Cleveland → Newark",
                origin="Chicago Hub (ORD-01)",
                destination="Newark Gateway (EWR-02)",
                estimated_distance=Decimal("1150.00"),
                estimated_duration=Decimal("17.50"),
                status="ACTIVE",
                is_active=True,
            )
            r2 = Route(
                name="I-95 North: Newark → Hartford → Boston",
                origin="Newark Gateway (EWR-02)",
                destination="Boston Terminal",
                estimated_distance=Decimal("360.00"),
                estimated_duration=Decimal("5.50"),
                status="ACTIVE",
                is_active=True,
            )
            r3 = Route(
                name="I-35 Corridor: Dallas → Waco → Austin",
                origin="Dallas Hub (DFW-04)",
                destination="Austin Retail Depot",
                estimated_distance=Decimal("310.00"),
                estimated_duration=Decimal("4.25"),
                status="ACTIVE",
                is_active=True,
            )
            db.add_all([r1, r2, r3])
            db.commit()
            print("Seeded 3 Freight Routes.")

        print("Demo data seeding completed successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
