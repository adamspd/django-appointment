"""appointments URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth import views as auth_views

from django.urls import include, path

from config.views import home



urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path(
        "staff/login/",
        auth_views.LoginView.as_view(
            template_name="staff_login.html",
            next_page="/app-admin/appointments/",
        ),
        name="staff_login",
    ),
    path("", include("appointment.urls")),
    prefix_default_language=False,
)