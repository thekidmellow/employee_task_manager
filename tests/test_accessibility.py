import json
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from axe_selenium_python import Axe
    AXE_AVAILABLE = True
except ImportError:
    AXE_AVAILABLE = False
    print("Warning: axe-selenium-python not installed. Install with: pip install axe-selenium-python")

from accounts.models import UserProfile
from tasks.models import Task


class AccessibilityTests(StaticLiveServerTestCase):
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        if not AXE_AVAILABLE:
            return
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        
        cls.driver = webdriver.Chrome(options=chrome_options)
        cls.driver.implicitly_wait(10)
        cls.axe = Axe(cls.driver)
    
    @classmethod
    def tearDownClass(cls):
        if AXE_AVAILABLE:
            cls.driver.quit()
        super().tearDownClass()
    
    def setUp(self):
        if not AXE_AVAILABLE:
            self.skipTest("axe-selenium-python not available")
        
        self.manager_user = User.objects.create_user(
            username='testmanager',
            email='manager@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Manager'
        )
        self.manager_user.userprofile.role = 'manager'
        self.manager_user.userprofile.save()
        
        self.employee_user = User.objects.create_user(
            username='testemployee',
            email='employee@test.com',
            password='testpass123',
            first_name='Test',
            last_name='Employee'
        )
        
        self.task = Task.objects.create(
            title='Accessibility Test Task',
            description='Task for accessibility testing',
            assigned_to=self.employee_user,
            created_by=self.manager_user,
            priority='medium',
            due_date='2024-12-31 23:59:59'
        )
    
    def login_user(self, username, password):
        self.driver.get(f'{self.live_server_url}/login/')
        
        username_field = self.driver.find_element(By.NAME, 'username')
        password_field = self.driver.find_element(By.NAME, 'password')
        
        username_field.send_keys(username)
        password_field.send_keys(password)
        
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        WebDriverWait(self.driver, 10).until(
            EC.url_changes(f'{self.live_server_url}/login/')
        )
    
    def test_homepage_accessibility(self):
        self.driver.get(self.live_server_url)
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0, 
                        f"Accessibility violations found: {json.dumps(violations, indent=2)}")
    
    def test_login_page_accessibility(self):
        self.driver.get(f'{self.live_server_url}/login/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Login page accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_registration_page_accessibility(self):
        self.driver.get(f'{self.live_server_url}/accounts/register/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Registration page accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_task_list_accessibility(self):
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/tasks/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Task list accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_task_detail_accessibility(self):
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/tasks/{self.task.id}/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Task detail accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_task_creation_accessibility(self):
        self.login_user('testmanager', 'testpass123')
        self.driver.get(f'{self.live_server_url}/tasks/create/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Task creation accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_manager_dashboard_accessibility(self):
        self.login_user('testmanager', 'testpass123')
        self.driver.get(f'{self.live_server_url}/dashboard/manager/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Manager dashboard accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_employee_dashboard_accessibility(self):
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/dashboard/employee/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Employee dashboard accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_profile_page_accessibility(self):
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/accounts/profile/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Profile page accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_error_pages_accessibility(self):
        self.driver.get(f'{self.live_server_url}/nonexistent-page/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"404 page accessibility violations: {json.dumps(violations, indent=2)}")
    
    def test_keyboard_navigation(self):
        self.driver.get(f'{self.live_server_url}/login/')
        
        username_field = self.driver.find_element(By.NAME, 'username')
        username_field.click()
        
        active_element = self.driver.switch_to.active_element
        self.assertEqual(active_element, username_field)
        
        active_element.send_keys('\t')
        password_field = self.driver.find_element(By.NAME, 'password')
        active_element = self.driver.switch_to.active_element
        self.assertEqual(active_element, password_field)
    
    def test_color_contrast(self):
        self.driver.get(self.live_server_url)
        
        self.axe.inject()
        
        results = self.axe.run({
            'tags': ['wcag2aa', 'wcag21aa'],
            'rules': {
                'color-contrast': {'enabled': True}
            }
        })
        
        violations = results['violations']
        contrast_violations = [v for v in violations if v['id'] == 'color-contrast']
        
        self.assertEqual(len(contrast_violations), 0,
                        f"Color contrast violations: {json.dumps(contrast_violations, indent=2)}")
    
    def test_heading_structure(self):
        self.login_user('testmanager', 'testpass123')
        self.driver.get(f'{self.live_server_url}/dashboard/manager/')
        
        self.axe.inject()
        
        results = self.axe.run({
            'rules': {
                'heading-order': {'enabled': True},
                'empty-heading': {'enabled': True}
            }
        })
        
        violations = results['violations']
        heading_violations = [v for v in violations if v['id'] in ['heading-order', 'empty-heading']]
        
        self.assertEqual(len(heading_violations), 0,
                        f"Heading structure violations: {json.dumps(heading_violations, indent=2)}")
    
    def test_form_labels(self):
        self.driver.get(f'{self.live_server_url}/accounts/register/')
        
        self.axe.inject()
        
        results = self.axe.run({
            'rules': {
                'label': {'enabled': True},
                'label-title-only': {'enabled': True}
            }
        })
        
        violations = results['violations']
        form_violations = [v for v in violations if v['id'] in ['label', 'label-title-only']]
        
        self.assertEqual(len(form_violations), 0,
                        f"Form label violations: {json.dumps(form_violations, indent=2)}")
    
    def test_image_alt_text(self):
        self.driver.get(self.live_server_url)
        
        self.axe.inject()
        
        results = self.axe.run({
            'rules': {
                'image-alt': {'enabled': True},
                'image-redundant-alt': {'enabled': True}
            }
        })
        
        violations = results['violations']
        image_violations = [v for v in violations if v['id'] in ['image-alt', 'image-redundant-alt']]
        
        self.assertEqual(len(image_violations), 0,
                        f"Image alt text violations: {json.dumps(image_violations, indent=2)}")
    
    def test_aria_attributes(self):
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/tasks/')
        
        self.axe.inject()
        
        results = self.axe.run({
            'tags': ['wcag2a', 'wcag2aa'],
            'rules': {
                'aria-allowed-attr': {'enabled': True},
                'aria-required-attr': {'enabled': True},
                'aria-valid-attr-value': {'enabled': True},
                'aria-valid-attr': {'enabled': True}
            }
        })
        
        violations = results['violations']
        aria_violations = [v for v in violations if 'aria' in v['id']]
        
        self.assertEqual(len(aria_violations), 0,
                        f"ARIA violations: {json.dumps(aria_violations, indent=2)}")
    
    def test_mobile_accessibility(self):
        self.driver.set_window_size(375, 667)
        
        self.login_user('testemployee', 'testpass123')
        self.driver.get(f'{self.live_server_url}/tasks/')
        
        self.axe.inject()
        results = self.axe.run()
        
        violations = results['violations']
        self.assertEqual(len(violations), 0,
                        f"Mobile accessibility violations: {json.dumps(violations, indent=2)}")
        
        self.driver.set_window_size(1920, 1080)


class ManualAccessibilityTests(StaticLiveServerTestCase):
    
    def test_screen_reader_compatibility(self):
        pass
    
    def test_keyboard_only_navigation(self):
        pass
    
    def test_high_contrast_mode(self):
        pass
    
    def test_zoom_functionality(self):
        pass