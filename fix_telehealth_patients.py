import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from telehealth.models import TelehealthSession
from appointments.models import Appointment
from django.db.models import Q

# Find sessions without patients
broken_sessions = TelehealthSession.objects.filter(patient__isnull=True)
print(f"Found {broken_sessions.count()} sessions without patients\n")

fixed_count = 0
for session in broken_sessions:
    # Try to find matching appointment
    appointment = Appointment.objects.filter(
        therapist=session.therapist,
        start_datetime=session.scheduled_at,
        is_telehealth=True
    ).first()
    
    if appointment and appointment.patient:
        session.patient = appointment.patient
        session.save()
        print(f"Fixed session {session.id}: Added patient {appointment.patient.get_full_name()}")
        fixed_count += 1
    else:
        print(f"Could not fix session {session.id}: No matching appointment found")

print(f"\nFixed {fixed_count} out of {broken_sessions.count()} sessions")
