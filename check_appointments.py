import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "theracare.settings")
django.setup()

from appointments.models import Appointment

print("Telehealth appointments:")
for apt in Appointment.objects.filter(is_telehealth=True).order_by("-created_at")[:10]:
    patient_name = apt.patient.get_full_name() if apt.patient else "No patient"
    therapist_name = apt.therapist.get_full_name() if apt.therapist else "No therapist"
    print(
        f"  Appt {str(apt.id)[:8]}: Patient={patient_name}, Therapist={therapist_name}, DateTime={apt.start_datetime}"
    )
