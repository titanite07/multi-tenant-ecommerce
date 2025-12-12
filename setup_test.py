import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce.settings')
django.setup()

from core.models import Tenant, User

tenant = Tenant.objects.filter(subdomain='teststore').first()
if not tenant:
    tenant = Tenant.objects.create(
        name='Test Store',
        subdomain='teststore',
        owner_email='owner@teststore.com'
    )
    print(f"Created tenant: {tenant.name}")
else:
    print(f"Tenant exists: {tenant.name}")

user = User.objects.filter(username='testadmin').first()
if not user:
    user = User.objects.create_user(
        username='testadmin',
        password='testpass123',
        email='admin@teststore.com',
        role='owner',
        tenant=tenant
    )
    print(f"Created user: {user.username}")
else:
    print(f"User exists: {user.username}")

print(f"\nTest credentials:")
print(f"  Username: testadmin")
print(f"  Password: testpass123")
print(f"  Tenant: {tenant.name}")
