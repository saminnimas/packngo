from django.contrib import admin
from .models import CustomUser

# Register your models here.
admin.site.register(CustomUser)
# can also add more customizing options along with register