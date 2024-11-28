from django.contrib.auth.models import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, username, is_active , level_access, password):
        user = self.model(username=username, is_active=is_active, level_access=level_access)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, is_active, level_access, password):
        user = self.model(username=username, is_active=is_active, level_access=level_access)
        user.set_password(password)
        user.is_superuser = True
        user.level_access = 10
        user.save(using=self._db)
        return user
