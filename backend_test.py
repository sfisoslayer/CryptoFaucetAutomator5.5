import requests
import json
import time
import sys
from datetime import datetime

class CryptoFaucetTester:
    def __init__(self, base_url="https://295ce8b4-f0a8-48d4-aa52-cd59839e8256.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session_id = None

    def run_test(self, name, method, endpoint, expected_status=200, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                print(f"❌ Unsupported method: {method}")
                return False, None

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_health_check(self):
        """Test API health check endpoint"""
        success, response = self.run_test(
            "API Health Check",
            "GET",
            "",
            200
        )
        if success:
            print(f"Response: {response}")
        return success

    def test_wallet_stats(self):
        """Test wallet statistics endpoint"""
        success, response = self.run_test(
            "Wallet Statistics",
            "GET",
            "wallet-stats",
            200
        )
        if success:
            print(f"Wallet Stats: Total Balance: {response.get('total_balance', 'N/A')}")
            print(f"Today's Claims: {response.get('total_claimed_today', 'N/A')}")
            print(f"Successful Claims: {response.get('successful_claims', 'N/A')}")
            print(f"Failed Claims: {response.get('failed_claims', 'N/A')}")
            print(f"Active Sessions: {response.get('active_sessions', 'N/A')}")
        return success

    def test_faucet_sites(self):
        """Test faucet sites list endpoint"""
        success, response = self.run_test(
            "Faucet Sites List",
            "GET",
            "faucet-sites",
            200
        )
        if success:
            print(f"Found {len(response)} faucet sites")
            if len(response) >= 21:
                print("✅ At least 21 faucet sites available as required")
            else:
                print(f"❌ Expected at least 21 faucet sites, but found {len(response)}")
                success = False
        return success

    def test_claim_logs(self):
        """Test claim logs endpoint"""
        success, response = self.run_test(
            "Claim Logs",
            "GET",
            "claim-logs",
            200
        )
        if success:
            print(f"Retrieved {len(response)} claim logs")
        return success

    def test_start_session(self, session_count=5):
        """Test starting a new session"""
        session_config = {
            "session_count": session_count,
            "auto_withdrawal": True,
            "withdrawal_threshold": 0.0000093,
            "withdrawal_address": "bc1qzh55yrw9z4ve9zxy04xuw9mq838g5c06tqvrxk",
            "proxy_enabled": True,
            "captcha_solving": True
        }
        
        success, response = self.run_test(
            f"Start Session with {session_count} sessions",
            "POST",
            "start-session",
            200,
            data=session_config
        )
        
        if success and 'session_id' in response:
            self.session_id = response['session_id']
            print(f"Session started with ID: {self.session_id}")
            print(f"Status: {response.get('status', 'N/A')}")
            print(f"Message: {response.get('message', 'N/A')}")
        return success

    def test_session_status(self):
        """Test session status endpoint"""
        if not self.session_id:
            print("❌ No active session ID to check status")
            return False
            
        success, response = self.run_test(
            "Session Status",
            "GET",
            f"session-status/{self.session_id}",
            200
        )
        
        if success:
            print(f"Session Status: {response.get('status', 'N/A')}")
            if 'stats' in response:
                stats = response['stats']
                print(f"Total Claims: {stats.get('total_claims', 'N/A')}")
                print(f"Successful Claims: {stats.get('successful_claims', 'N/A')}")
                print(f"Failed Claims: {stats.get('failed_claims', 'N/A')}")
                print(f"Total Earned: {stats.get('total_earned', 'N/A')}")
        return success

    def test_stop_session(self):
        """Test stopping a session"""
        if not self.session_id:
            print("❌ No active session ID to stop")
            return False
            
        success, response = self.run_test(
            "Stop Session",
            "DELETE",
            f"stop-session/{self.session_id}",
            200
        )
        
        if success:
            print(f"Response: {response}")
            self.session_id = None
        return success

def main():
    print("=" * 50)
    print("CRYPTO FAUCET AUTOMATION SYSTEM - API TESTING")
    print("=" * 50)
    
    tester = CryptoFaucetTester()
    
    # Test basic API endpoints
    tester.test_health_check()
    tester.test_wallet_stats()
    tester.test_faucet_sites()
    tester.test_claim_logs()
    
    # Test session management
    session_success = tester.test_start_session(session_count=5)
    
    if session_success:
        # Wait a bit for the session to initialize
        print("\nWaiting 5 seconds for session to initialize...")
        time.sleep(5)
        
        # Check session status
        tester.test_session_status()
        
        # Wait a bit more to see some activity
        print("\nWaiting 10 seconds to observe session activity...")
        time.sleep(10)
        
        # Check session status again
        tester.test_session_status()
        
        # Stop the session
        tester.test_stop_session()
    
    # Print results
    print("\n" + "=" * 50)
    print(f"TESTS PASSED: {tester.tests_passed}/{tester.tests_run}")
    print("=" * 50)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())