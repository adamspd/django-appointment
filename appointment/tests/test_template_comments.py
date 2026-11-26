from pathlib import Path

from django.test import SimpleTestCase

TEMPLATES = Path(__file__).resolve().parent.parent / 'templates'


class TemplateCommentTests(SimpleTestCase):
    """A {# #} comment must open and close on the same line: Django prints a comment that spans lines as text."""

    def test_comments_close_on_their_line(self):
        broken = []
        for template in sorted(TEMPLATES.rglob('*')):
            if not template.is_file():
                continue
            for number, line in enumerate(template.read_text(encoding='utf-8').splitlines(), start=1):
                if line.count('{#') != line.count('#}'):
                    broken.append(f'{template.relative_to(TEMPLATES)}:{number}')
        self.assertEqual(broken, [], 'Use {% comment %} ... {% endcomment %} for comments on several lines')
