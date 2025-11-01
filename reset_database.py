"""
Script to delete all users and create Adminsupport superuser.
Run this script on your production server after deploying the changes.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedex_clone.settings')
django.setup()

from core.models import UserProfile

def reset_users():
    """Delete all users and create Adminsupport superuser"""

    # Delete all existing users
    user_count = UserProfile.objects.count()
    UserProfile.objects.all().delete()
    print(f'✅ Successfully deleted {user_count} users')

    # Create Adminsupport superuser
    admin_user = UserProfile.objects.create_superuser(
        username='Adminsupport',
        email='admin@nexpress.com',
        password='Admin@2025',
        role='admin',
        first_name='Admin',
        last_name='Support'
    )

    print(f'\n✅ Successfully created superuser: {admin_user.username}')
    print('\n📝 Login credentials:')
    print('  Username: Adminsupport')
    print('  Email: admin@nexpress.com')
    print('  Password: Admin@2025')
    print('\n⚠️  IMPORTANT: Change this password immediately after first login!')
    print('\n🔗 Admin panel: https://nexpress.onrender.com/admin/')

if __name__ == '__main__':
    reset_users()
