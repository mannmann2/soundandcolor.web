from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
# from django.contrib.postgres.fields import ArrayField

# class Question(models.Model):

# 	question_text = models.CharField(max_length=200)
# 	pub_date = models.DateTimeField('date published')

# 	def __str__(self):
# 		return self.question_text

# 	def was_published_recently(self):
# 		return self.pub_date >= timezone.now() - datetime.timedelta(days=1)


class CustomUserManager(BaseUserManager):

    def _create_user(self, username, password, is_staff, is_superuser, **extra_fields):

        now = timezone.now()
        if not username:
            raise ValueError('The given username must be set')

        user = self.model(username=username, is_staff=is_staff, is_active=True,
                          is_superuser=is_superuser, last_login=now, date_joined=now, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        return self._create_user(username, password, False, False, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        return self._create_user(username, password, True, True, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):

    username = models.CharField(max_length=32, blank=True, unique=True)
    email = models.EmailField(max_length=254, blank=True)
    name = models.CharField(max_length=30, blank=True, null=True)
    uri = models.CharField(max_length=48, blank=True)
    # country = models.CharField(max_length=48, blank=True)
    # birthdate = models.CharField(max_length=48, blank=True)
    access_token = models.CharField(max_length=400)
    refresh_token = models.CharField(max_length=400)
    token = models.CharField(max_length=400, blank=True)
    scope = models.CharField(max_length=400, blank=True)

    friends = models.TextField(blank=True, default='')
    
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    # class Meta:
    #     verbose_name = _('user')
    #     verbose_name_plural = _('users')

    def __str__(self):
        return self.username
