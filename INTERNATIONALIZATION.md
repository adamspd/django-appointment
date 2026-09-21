# Internationalization (i18n) Guide 🌍

Django-Appointment includes built-in internationalization support with localized date formats, translations, and multi-language capabilities.

## Built-in Language Support 🗣️

Django-Appointment currently ships UI translations for:

| Language          | Code | Status                                                                |
|-------------------|------|-----------------------------------------------------------------------|
| English           | `en` | Default — the source strings                                          |
| French            | `fr` | Maintained by the project                                             |
| Spanish           | `es` | Contributed by @alexandermamaniy, **not actively maintained**         |

> **Spanish needs a maintainer.** The Spanish catalogue was contributed by @alexandermamaniy and is not kept up to
> date as the package changes, so newer strings may still show in English. It is shipped because a mostly-translated
> UI beats none at all. If you speak Spanish and would like to take it over, that would be very welcome — see
> [Contributing Translations](#contributing-translations) below, and please do open a PR.

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
    ('es', 'Spanish'),
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

The package includes date format patterns for 39 languages. No additional configuration needed!

## Contributing Translations 🤝

Want to add support for your language? We'd love your help!

### Adding a New Language

1. **Fork the repository** and create a new branch
2. **Generate translation files**:
   ```bash
   python manage.py makemessages -l [language_code]
   # Example: python manage.py makemessages -l es
   ```
3. **Translate the strings** in `appointment/locale/[language_code]/LC_MESSAGES/django.po`
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

## `gettext` or `gettext_lazy`? 🕐

Both mark a string for translation. They differ in **when** the translation happens, and
picking the wrong one is a quiet bug rather than a loud one.

| | Translates | Use it for |
|---|---|---|
| `gettext` | Immediately, when the line runs | Code that runs while answering a request |
| `gettext_lazy` | Later, when the string is displayed | Code that runs once, at import time |

The question to ask is: **does this line run at startup, or while answering somebody's
request?** Startup means there is no visitor yet, so there is no language to translate
into; `gettext` there would freeze whatever language happened to be active when Django
started. That is what `gettext_lazy` is for.

```python
# At import time -> lazy. There is no request yet.
class Appointment(models.Model):
    status = models.CharField(verbose_name=_("Status"))   # gettext_lazy

# While handling a request -> plain. The language is already known.
def save_appointment(request):
    messages.success(request, _("Appointment saved"))     # gettext
```

In this project that works out as:

- **`gettext_lazy`** — `models.py`, `forms.py`, `utils/validators.py`, `messages_.py`
  (field labels, form labels, validator messages, module-level constants)
- **`gettext`** — `views.py`, `views_admin.py`, `services.py`, `utils/session.py`,
  `utils/email_ops.py`, `utils/date_time.py`, `tasks.py` (everything built per request)

**Never import both under the same name.** The second one silently wins, so the file
claims one behaviour and has the other:

```python
# Wrong: every _() below is lazy, whatever the first import suggests
from django.utils.translation import gettext as _, gettext_lazy as _
```

One more thing worth knowing: `gettext_lazy` does not return a string, it returns a
placeholder that becomes one when displayed. Django handles that nearly everywhere, but
it can surprise code that expects real text — JSON serialisation, concatenation, or
anything writing straight to the database. When in doubt in request-time code, prefer
plain `gettext`.

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

Arabic, Bengali, Bulgarian, Chinese, Croatian, Czech, Danish, Dutch, English, Estonian, Finnish, French, German, Greek, Hebrew, Hindi, Hungarian, Indonesian, Italian, Japanese, Korean, Latvian, Lithuanian, Malay, Norwegian, Persian, Polish, Portuguese, Romanian, Russian, Serbian, Slovak, Slovenian, Spanish, Swedish, Thai, Turkish, Ukrainian, Vietnamese

That is 39 languages, defined in the `DATE_FORMATS` dictionary in
[`appointment/utils/date_time.py`](https://github.com/adamspd/django-appointment/blob/main/appointment/utils/date_time.py).
A date format is independent of the UI translation: adding an entry there localises how dates are displayed even
when no `.po` catalogue exists for that language.

Missing your language? Please contribute!
