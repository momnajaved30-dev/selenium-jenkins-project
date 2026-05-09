import unittest
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time

class EcommerceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up Chrome options for headless mode
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        # Automatically handle the download of the correct ChromeDriver
        cls.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        cls.driver.implicitly_wait(5)
        cls.base_url = "http://127.0.0.1:5000"

    @classmethod
    def tearDownClass(cls):
        cls.driver.quit()

    def test_01_homepage_load(self):
        print("Running homepage load test...")
        self.driver.get(f"{self.base_url}/")
        self.assertIn("ShopWave", self.driver.title)

    def test_02_product_search(self):
        print("Running product search test...")
        self.driver.get(f"{self.base_url}/")
        search_box = self.driver.find_element(By.NAME, "q")
        search_box.send_keys("Headphones")
        search_box.submit()
        self.assertIn("Headphones", self.driver.page_source)

    def test_03_product_display(self):
        print("Running product display test...")
        self.driver.get(f"{self.base_url}/")
        self.assertIn("Premium Wireless Headphones", self.driver.page_source)
        self.assertIn("79.99", self.driver.page_source)

    def test_04_product_detail_page(self):
        print("Running product detail page test...")
        self.driver.get(f"{self.base_url}/")
        product_link = self.driver.find_element(By.LINK_TEXT, "Premium Wireless Headphones")
        product_link.click()
        self.assertIn("Premium Wireless Headphones", self.driver.page_source)
        self.assertIn("Add to Cart", self.driver.page_source)

    def test_05_add_to_cart(self):
        print("Running add to cart test...")
        self.driver.get(f"{self.base_url}/product/1")
        add_button = self.driver.find_element(By.NAME, "quantity")
        add_button.clear()
        add_button.send_keys("2")
        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_btn.click()
        import time
        time.sleep(1)
        self.assertIn("Item added to cart!", self.driver.page_source)

    def test_06_view_cart(self):
        print("Running view cart test...")
        self.driver.get(f"{self.base_url}/cart")
        self.assertIn("Premium Wireless Headphones", self.driver.page_source)

    def test_07_checkout_invalid(self):
        print("Running invalid checkout test...")
        self.driver.get(f"{self.base_url}/checkout")
        # Bypass HTML5 validation to test server-side rejection
        self.driver.execute_script("document.getElementById('checkoutForm').setAttribute('novalidate', '');")
        # Click submit without filling required fields
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()
        # Should stay on checkout and show warning
        self.assertIn("Please fill in all required fields", self.driver.page_source)

    def test_08_checkout_valid(self):
        print("Running checkout test...")
        self.driver.get(f"{self.base_url}/checkout")
        self.driver.find_element(By.NAME, "name").send_keys("John Doe")
        self.driver.find_element(By.NAME, "email").send_keys("john@example.com")
        self.driver.find_element(By.NAME, "address").send_keys("123 Main St")
        self.driver.find_element(By.NAME, "phone").send_keys("1234567890")
        
        submit_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        submit_button.click()
        
        self.assertIn("Order Placed Successfully", self.driver.page_source)

    def test_09_remove_from_cart(self):
        print("Running remove from cart test...")
        # Since we checked out, the cart is empty. Let's add an item again to remove it.
        self.driver.get(f"{self.base_url}/product/2")
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        
        self.driver.get(f"{self.base_url}/cart")
        remove_link = self.driver.find_element(By.CSS_SELECTOR, "a.btn-outline-danger")
        remove_link.click()
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass
        self.assertIn("Item removed from cart.", self.driver.page_source)

    def test_10_admin_login(self):
        print("Running admin login test...")
        self.driver.get(f"{self.base_url}/admin_login")
        self.driver.find_element(By.NAME, "username").send_keys("admin")
        self.driver.find_element(By.NAME, "password").send_keys("store123")
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        import time
        time.sleep(1)
        self.assertIn("Admin Dashboard", self.driver.title)

    def test_11_admin_add_product(self):
        print("Running admin add product test...")
        self.driver.get(f"{self.base_url}/admin/product/add")
        name_field = self.driver.find_element(By.NAME, "name")
        name_field.clear()
        name_field.send_keys("Selenium Test Product")
        price_field = self.driver.find_element(By.NAME, "price")
        price_field.clear()
        price_field.send_keys("99.99")
        stock_field = self.driver.find_element(By.NAME, "stock")
        stock_field.clear()
        stock_field.send_keys("50")
        desc_field = self.driver.find_element(By.NAME, "description")
        desc_field.clear()
        desc_field.send_keys("Test description")
        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        self.driver.execute_script("arguments[0].click();", submit_btn)
        import time
        time.sleep(1) # Ensure page loads
        self.assertIn("added successfully", self.driver.page_source)

    def test_12_admin_edit_product(self):
        print("Running admin edit product test...")
        self.driver.get(f"{self.base_url}/admin_dashboard")
        # Find the newly added product and click its edit button
        row = self.driver.find_element(By.XPATH, "//td[contains(text(), 'Selenium Test Product')]/..")
        edit_link = row.find_element(By.XPATH, ".//a[contains(@href, '/admin/product/edit/')]")
        self.driver.execute_script("arguments[0].click();", edit_link)
        import time
        time.sleep(1)
        
        name_field = self.driver.find_element(By.NAME, "name")
        name_field.clear()
        name_field.send_keys("Updated Headphones")
        submit_btn = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        self.driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(1)
        self.assertIn("updated successfully", self.driver.page_source)

    def test_13_admin_update_order_status(self):
        print("Running admin update order status test...")
        self.driver.get(f"{self.base_url}/admin_dashboard")
        # Select 'Shipped' from the dropdown
        select = self.driver.find_element(By.NAME, "status")
        select.send_keys("Shipped")
        # Click the adjacent submit button using Javascript to bypass intercepted click issues
        submit_btn = select.find_element(By.XPATH, "./following-sibling::button")
        self.driver.execute_script("arguments[0].click();", submit_btn)
        import time
        time.sleep(1)
        self.assertIn("status updated to Shipped", self.driver.page_source)

    def test_14_admin_delete_product(self):
        print("Running admin delete product test...")
        self.driver.get(f"{self.base_url}/admin_dashboard")
        # Find the delete button for the product we just added and edited
        row = self.driver.find_element(By.XPATH, "//td[contains(text(), 'Updated Headphones')]/..")
        del_btn = row.find_element(By.XPATH, ".//form[contains(@action, '/admin/product/delete')]//button")
        self.driver.execute_script("arguments[0].click();", del_btn)
        import time
        time.sleep(1)
        # Accept alert if it's there
        try:
            alert = self.driver.switch_to.alert
            alert.accept()
        except:
            pass
        self.assertIn("deleted", self.driver.page_source)

    def test_15_user_logout(self):
        print("Running user logout test...")
        self.driver.get(f"{self.base_url}/admin_logout")
        self.assertIn("logged out", self.driver.page_source)

if __name__ == "__main__":
    unittest.main()
