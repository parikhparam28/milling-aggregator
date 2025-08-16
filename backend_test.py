#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime
import time
import io

class MillingAggregatorAPITester:
    def __init__(self, base_url="https://parts-mill-finder.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@example.com"
        self.user_password = "TestPass123!"
        
        # Store created resources for cleanup/reference
        self.created_rfq_id = None
        self.created_quote_ids = []
        self.created_order_id = None
        self.created_payment_id = None

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
            
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for multipart
                    if 'Content-Type' in test_headers:
                        del test_headers['Content-Type']
                    response = requests.post(url, data=data, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    self.log(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    self.log(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "",
            200
        )
        if success:
            expected_service = "milling-aggregator"
            if response.get('service') == expected_service:
                self.log(f"✅ Service name correct: {expected_service}")
                return True
            else:
                self.log(f"❌ Service name mismatch. Expected: {expected_service}, Got: {response.get('service')}")
        return False

    def test_register(self):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": self.user_email,
                "password": self.user_password,
                "name": "Test User"
            }
        )
        if success and response.get('email') == self.user_email:
            self.log(f"✅ User registered with email: {self.user_email}")
            return True
        return False

    def test_login(self):
        """Test user login and get token"""
        # Login uses form data, not JSON
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "username": self.user_email,
                "password": self.user_password
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.log(f"✅ Login successful, token obtained")
            return True
        return False

    def test_me_endpoint(self):
        """Test /me endpoint with token"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "me",
            200
        )
        if success and response.get('email') == self.user_email:
            self.log(f"✅ Current user endpoint working")
            return True
        return False

    def test_create_rfq(self):
        """Test RFQ creation with multipart form data"""
        # Create a simple test file
        test_file_content = b"Test CAD file content"
        files = {
            'cad_file': ('test.step', io.BytesIO(test_file_content), 'application/octet-stream')
        }
        
        form_data = {
            'material': 'Aluminum 6061',
            'quantity': '1',
            'tolerance': '±0.05 mm',
            'roughness': 'Ra 1.6 μm',
            'part_marking': 'false',
            'certification': 'None',
            'notes': 'Test RFQ for API testing'
        }
        
        success, response = self.run_test(
            "Create RFQ with File",
            "POST",
            "rfqs",
            200,
            data=form_data,
            files=files
        )
        
        if success and 'id' in response:
            self.created_rfq_id = response['id']
            self.log(f"✅ RFQ created with ID: {self.created_rfq_id}")
            return True
        return False

    def test_create_rfq_without_file(self):
        """Test RFQ creation without file"""
        form_data = {
            'material': 'Steel 304',
            'quantity': '5',
            'tolerance': '±0.1 mm',
            'roughness': 'Ra 3.2 μm',
            'part_marking': 'true',
            'certification': 'ISO 9001',
            'notes': 'Test RFQ without file'
        }
        
        success, response = self.run_test(
            "Create RFQ without File",
            "POST",
            "rfqs",
            200,
            data=form_data
        )
        
        if success and 'id' in response:
            self.log(f"✅ RFQ created without file, ID: {response['id']}")
            return True
        return False

    def test_list_rfqs(self):
        """Test listing user's RFQs"""
        success, response = self.run_test(
            "List RFQs",
            "GET",
            "rfqs",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"✅ Retrieved {len(response)} RFQs")
            return len(response) > 0
        return False

    def test_get_rfq(self):
        """Test getting specific RFQ"""
        if not self.created_rfq_id:
            self.log("❌ No RFQ ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Specific RFQ",
            "GET",
            f"rfqs/{self.created_rfq_id}",
            200
        )
        
        if success and response.get('id') == self.created_rfq_id:
            self.log(f"✅ Retrieved RFQ: {response.get('material')} x {response.get('quantity')}")
            return True
        return False

    def test_list_quotes(self):
        """Test listing quotes (should have auto-generated ones)"""
        # Wait a moment for quotes to be generated
        time.sleep(2)
        
        success, response = self.run_test(
            "List All Quotes",
            "GET",
            "quotes",
            200
        )
        
        if success and isinstance(response, list):
            self.created_quote_ids = [q['id'] for q in response]
            self.log(f"✅ Retrieved {len(response)} quotes")
            if len(response) >= 2:
                self.log("✅ Auto-generation of 2-3 quotes working")
                return True
            else:
                self.log("⚠️  Expected 2-3 auto-generated quotes")
        return False

    def test_list_quotes_filtered(self):
        """Test listing quotes filtered by RFQ"""
        if not self.created_rfq_id:
            return False
            
        success, response = self.run_test(
            "List Quotes Filtered by RFQ",
            "GET",
            f"quotes?rfq_id={self.created_rfq_id}",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"✅ Retrieved {len(response)} quotes for RFQ {self.created_rfq_id}")
            return True
        return False

    def test_accept_quote(self):
        """Test accepting a quote to create an order"""
        if not self.created_quote_ids:
            self.log("❌ No quote IDs available for testing")
            return False
            
        quote_id = self.created_quote_ids[0]
        success, response = self.run_test(
            "Accept Quote",
            "POST",
            f"quotes/{quote_id}/accept",
            200
        )
        
        if success and 'id' in response:
            self.created_order_id = response['id']
            self.log(f"✅ Order created with ID: {self.created_order_id}")
            self.log(f"   Status: {response.get('status')}")
            return response.get('status') == 'pending_payment'
        return False

    def test_list_orders(self):
        """Test listing orders"""
        success, response = self.run_test(
            "List Orders",
            "GET",
            "orders",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"✅ Retrieved {len(response)} orders")
            return len(response) > 0
        return False

    def test_pay_order(self):
        """Test paying for an order"""
        if not self.created_order_id:
            self.log("❌ No order ID available for testing")
            return False
            
        success, response = self.run_test(
            "Pay Order",
            "POST",
            f"orders/{self.created_order_id}/pay",
            200
        )
        
        if success and 'id' in response:
            self.created_payment_id = response['id']
            self.log(f"✅ Payment created with ID: {self.created_payment_id}")
            self.log(f"   Amount: €{response.get('amount', 0):.2f}")
            return response.get('status') == 'paid'
        return False

    def test_list_payments(self):
        """Test listing payments"""
        success, response = self.run_test(
            "List Payments",
            "GET",
            "payments",
            200
        )
        
        if success and isinstance(response, list):
            self.log(f"✅ Retrieved {len(response)} payments")
            return len(response) > 0
        return False

    def run_all_tests(self):
        """Run all API tests in sequence"""
        self.log("🚀 Starting Milling Aggregator API Tests")
        self.log(f"   Base URL: {self.base_url}")
        self.log(f"   API URL: {self.api_url}")
        self.log(f"   Test User: {self.user_email}")
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_register),
            ("User Login", self.test_login),
            ("Current User Info", self.test_me_endpoint),
            ("Create RFQ with File", self.test_create_rfq),
            ("Create RFQ without File", self.test_create_rfq_without_file),
            ("List RFQs", self.test_list_rfqs),
            ("Get Specific RFQ", self.test_get_rfq),
            ("List All Quotes", self.test_list_quotes),
            ("List Filtered Quotes", self.test_list_quotes_filtered),
            ("Accept Quote", self.test_accept_quote),
            ("List Orders", self.test_list_orders),
            ("Pay Order", self.test_pay_order),
            ("List Payments", self.test_list_payments),
        ]
        
        failed_tests = []
        
        for test_name, test_func in tests:
            self.log(f"\n{'='*60}")
            try:
                if not test_func():
                    failed_tests.append(test_name)
            except Exception as e:
                self.log(f"❌ {test_name} failed with exception: {str(e)}")
                failed_tests.append(test_name)
        
        # Print summary
        self.log(f"\n{'='*60}")
        self.log("📊 TEST SUMMARY")
        self.log(f"   Tests run: {self.tests_run}")
        self.log(f"   Tests passed: {self.tests_passed}")
        self.log(f"   Tests failed: {self.tests_run - self.tests_passed}")
        self.log(f"   Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if failed_tests:
            self.log(f"\n❌ Failed tests:")
            for test in failed_tests:
                self.log(f"   - {test}")
        else:
            self.log(f"\n✅ All tests passed!")
        
        return len(failed_tests) == 0

def main():
    tester = MillingAggregatorAPITester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())