from django.core.management.base import BaseCommand
from core.models import UserProfile


class Command(BaseCommand):
    help = 'Delete all users and create Adminsupport superuser'

    def handle(self, *args, **options):
        # Delete all existing users
        user_count = UserProfile.objects.count()
        UserProfile.objects.all().delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {user_count} users')
        )

        # Create Adminsupport superuser
        admin_user = UserProfile.objects.create_superuser(
            username='Adminsupport',
            email='admin@nexpress.com',
            password='Admin@2025',
            role='admin',
            first_name='Admin',
            last_name='Support'
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully created superuser: {admin_user.username}'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                '\nLogin credentials:'
            )
        )
        self.stdout.write(f'  Username: Adminsupport')
        self.stdout.write(f'  Email: admin@nexpress.com')
        self.stdout.write(f'  Password: Admin@2025')
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  IMPORTANT: Change this password immediately after first login!'
            )
        )
