from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()


class EmailBackend(ModelBackend):
    """
    Custom authentication backend that allows users to log in with email and password
    Also checks if email is verified before allowing login
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # username parameter might contain email
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        if username is None or password is None:
            return None

        try:
            # Try to find user by email
            user = UserModel.objects.get(Q(email__iexact=username) | Q(username__iexact=username))
        except UserModel.DoesNotExist:
            # Run the default password hasher to reduce timing attack
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # If multiple users have the same email, return None
            return None

        # Check password
        if user.check_password(password):
            return user

        return None
