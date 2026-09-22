from django.test import override_settings
from django.urls import reverse

from appointment.tests.base.base_test import BaseTest


def with_custom_templates(*names):
    """Register the given custom template names so the override lookup can find them.

    The locmem loader is listed before the app-directories one so the packaged defaults
    stay reachable: only the names given here are overridden, everything else falls back.
    """
    return override_settings(TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.locmem.Loader',
                 {f'custom/{name}': f'overridden {name}' for name in names}),
                'django.template.loaders.app_directories.Loader',
            ],
        },
    }])


class AdministrationTemplateOverrideTests(BaseTest):
    """The five administration pages must honour APPOINTMENT_CUSTOM_TEMPLATES_DIR like every other page."""

    def setUp(self):
        super().setUp()
        self.need_superuser_login()
        self.staff_user_id = self.users['staff1'].pk

    def urls(self):
        return {
            'staff_list.html': reverse('appointment:user_profile'),
            'user_profile.html': reverse('appointment:user_profile',
                                         kwargs={'staff_user_id': self.staff_user_id}),
            'manage_day_off.html': reverse('appointment:add_day_off_id',
                                           kwargs={'staff_user_id': self.staff_user_id}),
            'manage_unavailability.html': reverse('appointment:add_unavailability_id',
                                                  kwargs={'staff_user_id': self.staff_user_id}),
            'manage_working_hours.html': reverse('appointment:add_working_hours_id',
                                                 kwargs={'staff_user_id': self.staff_user_id}),
        }

    def test_defaults_are_used_when_no_override_exists(self):
        for name, url in self.urls().items():
            with self.subTest(template=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                used = [t.name for t in response.templates]
                self.assertIn(f'administration/{name}', used)
                self.assertNotIn(f'custom/{name}', used)

    def test_each_page_uses_its_override_when_one_exists(self):
        for name, url in self.urls().items():
            with self.subTest(template=name):
                with with_custom_templates(name):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.content, f'overridden {name}'.encode())

    def test_overriding_one_page_leaves_the_others_on_their_defaults(self):
        """A partial set of overrides must not disturb the pages it does not name."""
        urls = self.urls()
        with with_custom_templates('user_profile.html'):
            response = self.client.get(urls['user_profile.html'])
            self.assertEqual(response.content, b'overridden user_profile.html')

            response = self.client.get(urls['manage_day_off.html'])
            self.assertIn('administration/manage_day_off.html', [t.name for t in response.templates])

    def test_profile_error_page_uses_its_override(self):
        """The 403 a staff member gets on someone else's profile is overridable like every other error page."""
        self.need_staff_login()
        other_profile = reverse('appointment:user_profile',
                                kwargs={'staff_user_id': self.users['staff2'].pk})

        response = self.client.get(other_profile)
        self.assertIn('error_pages/403_forbidden.html', [t.name for t in response.templates])

        with with_custom_templates('403_forbidden.html'):
            response = self.client.get(other_profile)
            self.assertEqual(response.content, b'overridden 403_forbidden.html')

    @override_settings(APPOINTMENT_CUSTOM_TEMPLATES_DIR='my_templates')
    def test_custom_directory_setting_is_honoured(self):
        """The lookup must follow APPOINTMENT_CUSTOM_TEMPLATES_DIR, not the hardcoded 'custom'."""
        with override_settings(TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [],
            'OPTIONS': {
                'loaders': [
                    ('django.template.loaders.locmem.Loader',
                     {'my_templates/user_profile.html': 'from my_templates'}),
                    'django.template.loaders.app_directories.Loader',
                ],
            },
        }]):
            response = self.client.get(
                reverse('appointment:user_profile', kwargs={'staff_user_id': self.staff_user_id}))
            self.assertEqual(response.content, b'from my_templates')
