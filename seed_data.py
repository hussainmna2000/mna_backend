"""Seed initial data for MNA Real Estate & Construction."""
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.property import Property, PropertyType, PropertyStatus
from app.models.inquiry import Inquiry, InquiryStatus
from app.models.booking import SiteVisitBooking, BookingStatus
from app.utils.security import hash_password, generate_customer_id


def seed():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Super Admin
        admin_email = "admin@mna-realestate.com"
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(
                email=admin_email,
                full_name="MNA Principal Director",
                customer_id="MNA-ADMIN-001",
                hashed_password=hash_password("Admin@123"),
                role="superadmin",
                status="active",
                is_verified=True,
                phone="+91 8220000313",
            )
            db.add(admin)
            print("Created superadmin: admin@mna-realestate.com")

        # 2. Client User
        client_email = "client@mna-realestate.com"
        client = db.query(User).filter(User.email == client_email).first()
        if not client:
            client = User(
                email=client_email,
                full_name="John Smith",
                customer_id="MNA-2026-088",
                hashed_password=hash_password("Client@123"),
                role="client",
                status="active",
                is_verified=True,
                phone="+91 9876543210",
            )
            db.add(client)
            print("Created client: client@mna-realestate.com")

        db.commit()

        # 3. Properties
        properties_data = [
            {
                "slug": "mna-grandeur-residences",
                "title": "MNA Grandeur Residences",
                "tagline": "Ultra-Luxury Gated Community of 4BHK Bespoke Villas",
                "type": PropertyType.custom,
                "status": PropertyStatus.under_construction,
                "location": "Padiyur Ottapalayam, Tirupur",
                "city": "Padiyur Ottapalayam",
                "price_starting": "₹85 Lakhs",
                "price_numeric": 8500000.0,
                "bedrooms": "3 & 4 BHK",
                "carpet_area": "2,450 - 3,800 sq.ft",
                "possession_date": "December 2026",
                "completion_percentage": 78,
                "featured": True,
                "hero_image": "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?auto=format&fit=crop&w=1200&q=80",
                "rera_id": "TN/TIR/2026/04192",
                "architect": "Atelier Noir Architecture",
                "description": "An enclave of 24 bespoke standalone villas nestled amidst lush greenery in Padiyur Ottapalayam, featuring private lap pools, Italian marble, and integrated home automation.",
                "highlights": ["Private Swimming Pool", "Solar Microgrid Ready", "Double Height Living", "Vastu Compliant"],
                "amenities": ["Clubhouse", "24/7 Security", "Jogging Track", "Landscaped Gardens", "EV Charging Station"],
                "gallery_images": [
                    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=800&q=80",
                    "https://images.unsplash.com/photo-1600565193348-f74bd3c7ccdf?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "slug": "mna-emerald-heights",
                "title": "MNA Emerald Heights",
                "tagline": "Modern 2 & 3 BHK Contemporary Living",
                "type": PropertyType.bhk_2,
                "status": PropertyStatus.ready_to_move,
                "location": "Ganapathipalayam Road, Tirupur",
                "city": "Ganapathipalayam",
                "price_starting": "₹52 Lakhs",
                "price_numeric": 5200000.0,
                "bedrooms": "2 & 3 BHK",
                "carpet_area": "1,350 - 1,850 sq.ft",
                "possession_date": "Ready for Handover",
                "completion_percentage": 100,
                "featured": True,
                "hero_image": "https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?auto=format&fit=crop&w=1200&q=80",
                "rera_id": "TN/TIR/2025/03180",
                "architect": "S&P Design Studio",
                "description": "Ready to move premium apartments with world-class amenities, scenic views, and seamless connectivity to Kangeyam Road.",
                "highlights": ["Rooftop Infinity Pool", "Gym & Yoga Studio", "Kids Play Area", "CCTV Surveillance"],
                "amenities": ["Covered Car Parking", "High Speed Lifts", "Power Backup", "Rainwater Harvesting"],
                "gallery_images": [
                    "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80"
                ]
            },
            {
                "slug": "mna-serene-valley-plots",
                "title": "MNA Serene Valley Plots",
                "tagline": "DTCP & RERA Approved Premium Residential Plots",
                "type": PropertyType.land,
                "status": PropertyStatus.ready_to_move,
                "location": "Ottapalayam Main Junction, Padiyur",
                "city": "Padiyur Ottapalayam",
                "price_starting": "₹28 Lakhs",
                "price_numeric": 2800000.0,
                "bedrooms": "Plots",
                "carpet_area": "1,200 - 4,800 sq.ft",
                "possession_date": "Immediate Registration",
                "completion_percentage": 100,
                "featured": True,
                "hero_image": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?auto=format&fit=crop&w=1200&q=80",
                "rera_id": "TN/TIR/2026/01004",
                "architect": "Urban Earth Consultants",
                "description": "Gated residential plots with 40ft blacktop tar roads, underground electricity cabling, individual water tap connections, and grand entrance arch.",
                "highlights": ["Clear Legal Titles", "Bank Loan Arranged", "Avenue Tree Plantation", "Street Lights"],
                "amenities": ["Gated Perimeter Wall", "Water Storage Tank", "Children's Park"],
                "gallery_images": []
            },
            {
                "slug": "mna-royal-crest-villas",
                "title": "MNA Royal Crest Villas",
                "tagline": "Exclusive 3BHK Independent Duplex Homes",
                "type": PropertyType.custom,
                "status": PropertyStatus.upcoming,
                "location": "Padiyur Garden Area, Tirupur",
                "city": "Padiyur Ottapalayam",
                "price_starting": "₹68 Lakhs",
                "price_numeric": 6800000.0,
                "bedrooms": "3 BHK Duplex",
                "carpet_area": "1,980 sq.ft",
                "possession_date": "March 2027",
                "completion_percentage": 25,
                "featured": False,
                "hero_image": "https://images.unsplash.com/photo-1580587771525-78b9dba3b914?auto=format&fit=crop&w=1200&q=80",
                "rera_id": "TN/TIR/2026/05821",
                "architect": "Vanguard Architectural Labs",
                "description": "Pre-launching modern duplex villas with customized floor plans, private terrace garden, and premium teak finish doors.",
                "highlights": ["Modular Kitchen Included", "Solar Water Heater", "Individual Borewell"],
                "amenities": ["24hr Security", "Wide Concrete Roads", "Lush Landscape"],
                "gallery_images": []
            }
        ]

        created_props = []
        for pdata in properties_data:
            existing_p = db.query(Property).filter(Property.slug == pdata["slug"]).first()
            if not existing_p:
                prop = Property(**pdata)
                db.add(prop)
                db.commit()
                db.refresh(prop)
                created_props.append(prop)
                print(f"Created property: {prop.title}")
            else:
                created_props.append(existing_p)

        # 4. Sample Inquiry
        first_inquiry = db.query(Inquiry).first()
        if not first_inquiry:
            inquiry1 = Inquiry(
                name="Senthil Kumar",
                email="senthil.k@gmail.com",
                phone="+91 9443212345",
                interest="3BHK Villa at MNA Grandeur",
                message="Interested in visiting the sample villa this Saturday afternoon with family. Please share brochure and price breakdown.",
                status=InquiryStatus.new,
                source="contact_form",
                admin_notes="Follow up via WhatsApp and confirm site visit.",
            )
            inquiry2 = Inquiry(
                name="Deepa Raman",
                email="deepa.raman@yahoo.com",
                phone="+91 9842109876",
                interest="Serene Valley Residential Plot",
                message="Looking for an east-facing corner plot around 2,400 sq.ft for immediate construction.",
                status=InquiryStatus.contacted,
                source="contact_form",
                admin_notes="Brochure sent. Client requested bank loan assistance documentation.",
            )
            db.add_all([inquiry1, inquiry2])
            db.commit()
            print("Created sample inquiries.")

        # 5. Sample Bookings
        first_booking = db.query(SiteVisitBooking).first()
        if not first_booking and created_props:
            booking1 = SiteVisitBooking(
                visitor_name="Dr. Rajeshwar Murthy",
                visitor_email="dr.murthy@apollo.org",
                visitor_phone="+91 9790012345",
                property_id=created_props[0].id,
                visit_date=date.today() + timedelta(days=2),
                visit_time="11:00 AM",
                status=BookingStatus.confirmed,
                notes="Family visit. Interested in Villa 14 or 15.",
                admin_notes="Sales manager assigned for walkthrough.",
            )
            booking2 = SiteVisitBooking(
                visitor_name="Anand Sundaram",
                visitor_email="anand.s@tcs.com",
                visitor_phone="+91 9884011223",
                property_id=created_props[1].id if len(created_props) > 1 else created_props[0].id,
                visit_date=date.today() + timedelta(days=4),
                visit_time="03:30 PM",
                status=BookingStatus.pending,
                notes="Weekend inspection with architect.",
            )
            db.add_all([booking1, booking2])
            db.commit()
            print("Created sample site visit bookings.")

        print("Seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
