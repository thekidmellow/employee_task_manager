from django.test import TestCase
from django.urls import resolve


class CoreViewsTests(TestCase):
    def test_home_page_loads(self):
        # TODO: change "home" to whatever your home url name is if needed
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        # TODO: adjust template if needed
        self.assertTemplateUsed(r, "core/home.html")
