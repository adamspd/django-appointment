# Internationalization (i18n) Guide 🌍

Django-Appointment includes built-in internationalization support with localized date formats, translations, and multi-language capabilities.

## Built-in Language Support 🗣️

Django-Appointment currently includes translations for:
- **English** (en) - Default
- **French** (fr) - Complete translation

## Quick Setup

### 1. Enable Internationalization in Django

Add these settings to your `settings.py`:

```python
# Internationalization
LANGUAGE_CODE = 'en'  # Default language
USE_I18N = True       # Enable translations
USE_L10N = True       # Enable localized formatting
USE_TZ = True         # Enable timezone support

# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'French'),
    # Add more languages as needed
]

# Translation files location
LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

### 2. Add Middleware

Add the locale middleware to your `MIDDLEWARE` setting:

```python
MIDDLEWARE = [
    # ... other middleware
    'django.middleware.locale.LocaleMiddleware',
    # ... other middleware
]
```

### 3. Language Switching

Include language switching in your URLs:

```python
# urls.py
from django.conf.urls.i18n import i18n_patterns
from django.urls import path, include

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
]

urlpatterns += i18n_patterns(
    path('appointment/', include('appointment.urls')),
    # ... other URL patterns
)
```

## Localized Date Formats 📅

Django-Appointment automatically formats dates according to the user's language:

- **English**: "Thu, August 14, 2025"
- **French**: "jeu 14 août 2025"
- **German**: "Do, 14. August 2025"
- **Spanish**: "jue, 14 de agosto de 2025"

The package includes date format patterns for 35+ languages. No additional configuration needed!

## Contributing Translations 🤝

Want to add support for your language? We'd love your help!

### Adding a New Language

1. **Fork the repository** and create a new branch
2. **Generate translation files**:
   ```bash
   python manage.py makemessages -l [language_code]
   # Example: python manage.py makemessages -l es
   ```
3. **Translate the strings** in `locale/[language_code]/LC_MESSAGES/django.po`
4. **Add date format** to `appointment/utils/date_time.py` in the `DATE_FORMATS` dictionary
5. **Test your translations**:
   ```bash
   python manage.py compilemessages
   ```
6. **Submit a pull request**

### Translation Guidelines

- Use formal tone for UI elements
- Keep technical terms consistent
- Test date formats with real examples
- Include gender-neutral language where possible

## Advanced: Translating Database Content 🗃️

For translating service names, descriptions, and other database content, you can use third-party packages:

### Option 1: django-modeltranslation

1. **Install the package**:
   ```bash
   pip install django-modeltranslation
   ```

2. **Add to INSTALLED_APPS**:
   ```python
   INSTALLED_APPS = [
       'modeltranslation',
       'appointment',  # Must come after modeltranslation
       # ... other apps
   ]
   ```

3. **Create translation configuration**:
   ```python
   # translation.py (in your project root)
   from modeltranslation.translator import translator, TranslationOptions
   from appointment.models import Service

   class ServiceTranslationOptions(TranslationOptions):
       fields = ('name', 'description')

   translator.register(Service, ServiceTranslationOptions)
   ```

4. **Generate and run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

### Option 2: django-parler

1. **Install the package**:
   ```bash
   pip install django-parler
   ```

2. **Follow django-parler documentation** for setup and configuration

## Language-Specific Features 🎯

### Right-to-Left (RTL) Languages

Django-Appointment includes basic RTL support for languages like Arabic and Hebrew. The date formats are properly configured for RTL display.

### Pluralization

The package correctly handles plural forms for time durations:
- English: "1 hour" vs "2 hours"
- French: "1 heure" vs "2 heures"
- And more complex rules for languages like Russian or Arabic

## Troubleshooting 🔧

### Common Issues

1. **Dates showing in wrong format**:
   - Ensure `USE_L10N = True` in settings
   - Check that locale middleware is enabled
   - Verify language code is supported

2. **Translations not appearing**:
   - Run `python manage.py compilemessages`
   - Check `LOCALE_PATHS` setting
   - Verify middleware order

3. **Mixed language content**:
   - Database content requires separate translation (see above)
   - UI elements use Django's translation system

### Getting Help

- Check the [main documentation](https://django-appt-doc.adamspierredavid.com)
- Open an issue on [GitHub](https://github.com/adamspd/django-appointment/issues)
- Join the discussion in our [community](https://github.com/adamspd/django-appointment/discussions)

## Supported Date Format Languages 📊

Currently includes date format patterns for:

Arabic, Bengali, Bulgarian, Chinese, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hebrew, Hindi, Croatian, Hungarian, Indonesian, Italian, Japanese, Korean, Latvian, Lithuanian, Malay, Norwegian, Polish, Portuguese, Romanian, Russian, Slovak, Slovenian, Serbian, Spanish, Swedish, Thai, Turkish, Ukrainian, Vietnamese

Missing your language? Please contribute!
