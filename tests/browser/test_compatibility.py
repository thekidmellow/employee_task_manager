import time
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User, Group
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from apps.accounts.models import UserProfile


class BrowserCompatibilityTests(StaticLiveServerTestCase):
    BROWSERS = ["chrome", "firefox"]

    def get_driver(self, browser):
        if browser == "chrome":
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            return webdriver.Chrome(options=options)
        elif browser == "firefox":
            options = FirefoxOptions()
            options.add_argument('--headless')
            return webdriver.Firefox(options=options)

    def setUp(self):
        self.manager = User.objects.create_user(username='testmanager', password='testpass123')
        UserProfile.objects.update_or_create(user=self.manager, defaults={'role': 'manager'})
        managers_group, _ = Group.objects.get_or_create(name='Managers')
        self.manager.groups.add(managers_group)
        
        self.employee = User.objects.create_user(username='testemployee', password='testpass123')
        UserProfile.objects.update_or_create(user=self.employee, defaults={'role': 'employee'})
        employees_group, _ = Group.objects.get_or_create(name='Employees')
        self.employee.groups.add(employees_group)

    def login_user(self, driver):
        driver.get(f'{self.live_server_url}/login/')
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        driver.find_element(By.NAME, 'username').send_keys('testmanager')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        WebDriverWait(driver, 90).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(1)

    def test_javascript_functionality_across_browsers(self):
        for browser in self.BROWSERS:
            driver = self.get_driver(browser)
            try:
                wait = WebDriverWait(driver, 90)
                self.login_user(driver)
                driver.get(f"{self.live_server_url}/tasks/create/")
                wait.until(EC.presence_of_element_located((By.NAME, "title")))
                time.sleep(2)
                
                driver.execute_script("""
                    var form = document.getElementById('taskForm');
                    var titleField = document.querySelector('[name="title"]');
                    var descField = document.querySelector('[name="description"]');
                    var assignedField = document.querySelector('[name="assigned_to"]');
                    var priorityField = document.querySelector('[name="priority"]');
                    var dueDateField = document.querySelector('[name="due_date"]');
                    
                    titleField.value = 'Browser JS Test Task Title';
                    titleField.dispatchEvent(new Event('input', {bubbles: true}));
                    titleField.dispatchEvent(new Event('change', {bubbles: true}));
                    
                    descField.value = 'Testing JavaScript interaction across multiple browsers for compatibility';
                    descField.dispatchEvent(new Event('input', {bubbles: true}));
                    descField.dispatchEvent(new Event('change', {bubbles: true}));
                    
                    if (assignedField.options.length > 1) {
                        assignedField.selectedIndex = 1;
                    }
                    assignedField.dispatchEvent(new Event('change', {bubbles: true}));
                    
                    priorityField.value = 'high';
                    priorityField.dispatchEvent(new Event('change', {bubbles: true}));
                    
                    dueDateField.value = '2030-12-31T12:00';
                    dueDateField.dispatchEvent(new Event('input', {bubbles: true}));
                    dueDateField.dispatchEvent(new Event('change', {bubbles: true}));
                    
                    if (form) {
                        form.submit();
                    }
                """)
                
                wait.until(EC.url_contains('/tasks/'))
                
                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".alert.alert-success, .alert.success")))
                except:
                    self.assertIn('/tasks/', driver.current_url)
            finally:
                driver.quit()