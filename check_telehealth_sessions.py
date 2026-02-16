import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'theracare.settings')
django.setup()

from telehealth.models import TelehealthSession

print("Total sessions:", TelehealthSession.objects.count())
print("\nAll telehealth sessions:")
for s in TelehealthSession.objects.all():
    patient_name = s.patient.get_full_name() if s.patient else "No patient"
    therapist_name = s.therapist.get_full_name() if s.therapist else "No therapist"
    print(f"  Session {s.id}: Patient={patient_name}, Therapist={therapist_name}, Status={s.status}")
