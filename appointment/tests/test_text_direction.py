from django.template.loader import render_to_string
from django.test import TestCase
from django.utils import translation


class TextDirectionTests(TestCase):
    """Pages and emails are written right to left in languages like Arabic, Hebrew and Persian."""

    def render(self, template, language):
        with translation.override(language):
            return render_to_string(template, {})

    def test_page_follows_the_language(self):
        self.assertIn('<html lang="ar" dir="rtl">', self.render('base_templates/base.html', 'ar'))
        self.assertIn('<html lang="fr" dir="ltr">', self.render('base_templates/base.html', 'fr'))

    def test_email_follows_the_language(self):
        html = self.render('email_sender/base_email.html', 'he')
        self.assertIn('<html lang="he" dir="rtl">', html)
        # Mail clients often drop the attributes of <html>
        self.assertIn('style="background-color: #f4f6fa;" dir="rtl"', html)
        self.assertIn('dir="ltr"', self.render('email_sender/base_email.html', 'en'))

    def test_thank_you_badge_keeps_its_space_on_the_title_side(self):
        self.assertIn('style="padding-left: 18px;"', self.render('email_sender/thank_you_email.html', 'ar'))
        self.assertIn('style="padding-right: 18px;"', self.render('email_sender/thank_you_email.html', 'en'))
