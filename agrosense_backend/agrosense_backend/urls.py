from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # forward all api routes to api app
    path('api/', include('api.urls')),
]