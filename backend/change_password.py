import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
django.setup()

User = get_user_model()
try:
    user = User.objects.get(username='admin')
    user.set_password('admin')
    user.save()
    print("Password for 'admin' changed successfully.")
except User.DoesNotExist:
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser 'admin' created successfully.")