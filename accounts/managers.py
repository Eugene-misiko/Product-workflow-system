from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):

    def create_user(self, first_name, email=None, password=None, **extra_fields):
        """
        Create and return a regular user using first_name instead of username.
        """
        if not first_name:
            raise ValueError("First name is required")
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(
            first_name=first_name,
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, first_name, email=None, password=None, **extra_fields):
        """
        Create and return a superuser.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(first_name, email, password, **extra_fields)