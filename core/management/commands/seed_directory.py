from django.core.management.base import BaseCommand
from django.db import transaction

from departments.models import Department
from offices.models import Office, Service
from staff.models import Staff

# Department names are public (kisii.go.ke). Codes are our own short labels.
DEPARTMENTS = [
    ("AGR", "Agriculture, Fisheries, Livestock Development and Irrigation"),
    ("EDU", "Education, Technical Training, Innovation and Social Sciences"),
    ("FIN", "Finance, Economic Planning and ICT Services"),
    ("INF", "Infrastructure, Energy and Public Works"),
    ("LND", "Lands, Physical Planning, Housing and Urban Development"),
    ("MED", "Medical Services, Public Health and Sanitation"),
    ("TRD", "Trade, Tourism, Industry and Marketing"),
    ("WAT", "Water, Environment, Natural Resources and Climate Change"),
    (
        "PSA",
        "Public Service, County Administration and Participatory Development, "
        "Office of the Governor",
    ),
    ("YSC", "Youth, Sports, Culture, Arts and Special Services"),
]

SERVICES = [
    "Public enquiries",
    "Records and registry",
    "Licensing and permits",
    "Revenue and payments",
    "ICT support",
]

# name, department code, building, floor/room, extension, email, services
# Office names are real; buildings, extensions and emails are dummy data.
OFFICES = [
    ("Office of the Governor", "PSA", "Sample Block A", "Ground floor", "101",
     "governor.office@example.go.ke", ["Public enquiries"]),
    ("Office of the Deputy Governor", "PSA", "Sample Block A", "Ground floor", "102",
     "deputy.governor@example.go.ke", ["Public enquiries"]),
    ("Office of the County Secretary", "PSA", "Sample Block A", "First floor", "103",
     "county.secretary@example.go.ke", ["Public enquiries", "Records and registry"]),
    ("County Public Service Board", "PSA", "Sample Block B", "First floor", "201",
     "service.board@example.go.ke", ["Records and registry"]),
    ("Kisii Municipality", "LND", "Sample Block C", "Ground floor", "301",
     "kisii.municipality@example.go.ke", ["Licensing and permits", "Public enquiries"]),
    ("Ogembo Municipality", "LND", "Sample Block C", "Ground floor", "302",
     "ogembo.municipality@example.go.ke", ["Licensing and permits", "Public enquiries"]),
]

DESIGNATIONS = [
    "Administrative Officer",
    "Records Officer",
    "ICT Officer",
    "Clerical Officer",
    "Senior Officer",
]


class Command(BaseCommand):
    help = "Load sample directory data: public department names plus dummy offices and staff."

    @transaction.atomic
    def handle(self, *args, **options):
        departments = {}
        for code, name in DEPARTMENTS:
            department, _ = Department.objects.update_or_create(
                code=code, defaults={"name": name}
            )
            departments[code] = department

        services = {
            name: Service.objects.get_or_create(name=name)[0] for name in SERVICES
        }

        offices = []
        for name, code, building, room, ext, email, service_names in OFFICES:
            office, _ = Office.objects.update_or_create(
                department=departments[code],
                name=name,
                defaults={
                    "building": building,
                    "floor_room": room,
                    "phone_ext": ext,
                    "email": email,
                },
            )
            office.services.set([services[s] for s in service_names])
            offices.append(office)

        for n in range(1, 25):
            office = offices[n % len(offices)]
            Staff.objects.update_or_create(
                work_email=f"sample.officer{n:02d}@example.go.ke",
                defaults={
                    "full_name": f"Sample Officer {n:02d}",
                    "designation": DESIGNATIONS[n % len(DESIGNATIONS)],
                    "department": office.department,
                    "office": office,
                    "work_phone": f"+2547000000{n:02d}",
                },
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {Department.objects.count()} departments, "
                f"{Office.objects.count()} offices, "
                f"{Staff.objects.count()} staff."
            )
        )