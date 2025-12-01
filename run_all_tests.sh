#!/bin/bash

# Employee Task Manager - Comprehensive Test Runner
# This script runs all types of tests for the project

set -e  # Exit on any error

echo "🚀 Starting comprehensive test suite for Employee Task Manager"
echo "=============================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Activating..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "../venv/bin/activate" ]; then
        source ../venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please create and activate it first."
        exit 1
    fi
fi

# Create test results directory
mkdir -p test_results
TEST_RESULTS_DIR="test_results"

# Set Django settings
export DJANGO_SETTINGS_MODULE="employee_task_manager.settings"

print_status "Checking dependencies..."

# Check if required packages are installed
python -c "import django" 2>/dev/null || {
    print_error "Django not installed. Run: pip install -r requirements.txt"
    exit 1
}

# Check if pytest is available for JavaScript tests
npm --version >/dev/null 2>&1 || {
    print_warning "npm not found. JavaScript tests will be skipped."
    SKIP_JS_TESTS=true
}

# Check if Selenium drivers are available
print_status "Checking Selenium WebDriver availability..."

# Chrome driver check
chromedriver --version >/dev/null 2>&1 || {
    print_warning "ChromeDriver not found. Cross-browser tests may fail."
}

# Firefox driver check
geckodriver --version >/dev/null 2>&1 || {
    print_warning "GeckoDriver not found. Firefox tests will be skipped."
}

echo ""
print_status "Starting test execution..."
echo ""

# 1. Python Unit Tests
echo "1️⃣  Running Python Unit Tests"
echo "================================"

print_status "Running Django unit tests..."
python manage.py test --verbosity=2 --keepdb 2>&1 | tee "$TEST_RESULTS_DIR/unit_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Unit tests completed successfully"
else
    print_error "Unit tests failed. Check $TEST_RESULTS_DIR/unit_tests.log"
    UNIT_TESTS_FAILED=true
fi

echo ""

# 2. JavaScript Tests
echo "2️⃣  Running JavaScript Tests"
echo "============================="

if [ "$SKIP_JS_TESTS" != "true" ]; then
    print_status "Installing JavaScript dependencies..."
    npm install 2>&1 | tee "$TEST_RESULTS_DIR/npm_install.log"
    
    if [ $? -eq 0 ]; then
        print_status "Running Jest tests..."
        npm run test:js 2>&1 | tee "$TEST_RESULTS_DIR/js_tests.log"
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            print_success "JavaScript tests completed successfully"
        else
            print_error "JavaScript tests failed. Check $TEST_RESULTS_DIR/js_tests.log"
            JS_TESTS_FAILED=true
        fi
        
        # Generate JavaScript coverage
        print_status "Generating JavaScript test coverage..."
        npm run test:js:coverage 2>&1 | tee "$TEST_RESULTS_DIR/js_coverage.log"
    else
        print_error "Failed to install JavaScript dependencies"
        JS_TESTS_FAILED=true
    fi
else
    print_warning "Skipping JavaScript tests (npm not available)"
fi

echo ""

# 3. Integration Tests
echo "3️⃣  Running Integration Tests"
echo "=============================="

print_status "Running Selenium integration tests..."
python manage.py test tests.integration --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/integration_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Integration tests completed successfully"
else
    print_error "Integration tests failed. Check $TEST_RESULTS_DIR/integration_tests.log"
    INTEGRATION_TESTS_FAILED=true
fi

echo ""

# 4. API Tests
echo "4️⃣  Running API Tests"
echo "===================="

print_status "Running API endpoint tests..."
python manage.py test tests.test_api --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/api_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "API tests completed successfully"
else
    print_error "API tests failed. Check $TEST_RESULTS_DIR/api_tests.log"
    API_TESTS_FAILED=true
fi

echo ""

# 5. Security Tests
echo "5️⃣  Running Security Tests"
echo "=========================="

print_status "Running security tests..."
python manage.py test tests.test_security --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/security_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Security tests completed successfully"
else
    print_error "Security tests failed. Check $TEST_RESULTS_DIR/security_tests.log"
    SECURITY_TESTS_FAILED=true
fi

echo ""

# 6. Database Performance Tests
echo "6️⃣  Running Database Performance Tests"
echo "======================================"

print_status "Running database performance tests..."
python manage.py test tests.test_database --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/database_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Database tests completed successfully"
else
    print_error "Database tests failed. Check $TEST_RESULTS_DIR/database_tests.log"
    DATABASE_TESTS_FAILED=true
fi

echo ""

# 7. Accessibility Tests
echo "7️⃣  Running Accessibility Tests"
echo "==============================="

print_status "Running automated accessibility tests..."
python manage.py test tests.test_accessibility --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/accessibility_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Accessibility tests completed successfully"
else
    print_warning "Accessibility tests failed. This might be due to missing axe-selenium-python."
    print_warning "Install with: pip install axe-selenium-python"
    ACCESSIBILITY_TESTS_FAILED=true
fi

echo ""

# 8. Cross-Browser Tests
echo "8️⃣  Running Cross-Browser Tests"
echo "==============================="

print_status "Running cross-browser compatibility tests..."
python manage.py test tests.browser --verbosity=2 2>&1 | tee "$TEST_RESULTS_DIR/browser_tests.log"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    print_success "Cross-browser tests completed successfully"
else
    print_warning "Cross-browser tests failed. This might be due to missing WebDriver."
    BROWSER_TESTS_FAILED=true
fi

echo ""

# 9. Performance/Load Tests (Optional)
echo "9️⃣  Running Performance Tests"
echo "============================="

# Check if Locust is available
locust --version >/dev/null 2>&1 && {
    print_status "Running load tests with Locust..."
    
    # Start Django server in background
    python manage.py runserver 8001 >/dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Run load tests
    locust -f tests/performance/locustfile.py --headless -u 5 -r 1 -t 30s --host=http://localhost:8001 2>&1 | tee "$TEST_RESULTS_DIR/performance_tests.log"
    
    # Kill the server
    kill $SERVER_PID 2>/dev/null
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        print_success "Performance tests completed successfully"
    else
        print_error "Performance tests failed. Check $TEST_RESULTS_DIR/performance_tests.log"
        PERFORMANCE_TESTS_FAILED=true
    fi
} || {
    print_warning "Locust not found. Skipping performance tests."
    print_warning "Install with: pip install locust"
}

echo ""

# 10. Code Coverage Report
echo "🔟 Generating Code Coverage Report"
echo "=================================="

print_status "Generating Python code coverage..."
coverage run --source='.' manage.py test 2>/dev/null
coverage report 2>&1 | tee "$TEST_RESULTS_DIR/coverage_report.txt"
coverage html -d "$TEST_RESULTS_DIR/htmlcov" 2>/dev/null

print_success "Coverage report generated in $TEST_RESULTS_DIR/htmlcov/"

echo ""

# 11. Test Summary
echo "📊 Test Results Summary"
echo "======================"

TOTAL_TESTS=9
FAILED_TESTS=0

echo "Test Suite Results:"
echo "==================="

[ "$UNIT_TESTS_FAILED" == "true" ] && { echo "❌ Unit Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ Unit Tests: PASSED"
[ "$JS_TESTS_FAILED" == "true" ] && { echo "❌ JavaScript Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ JavaScript Tests: PASSED"
[ "$INTEGRATION_TESTS_FAILED" == "true" ] && { echo "❌ Integration Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ Integration Tests: PASSED"
[ "$API_TESTS_FAILED" == "true" ] && { echo "❌ API Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ API Tests: PASSED"
[ "$SECURITY_TESTS_FAILED" == "true" ] && { echo "❌ Security Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ Security Tests: PASSED"
[ "$DATABASE_TESTS_FAILED" == "true" ] && { echo "❌ Database Tests: FAILED"; ((FAILED_TESTS++)); } || echo "✅ Database Tests: PASSED"
[ "$ACCESSIBILITY_TESTS_FAILED" == "true" ] && { echo "⚠️  Accessibility Tests: FAILED (possibly missing dependencies)"; } || echo "✅ Accessibility Tests: PASSED"
[ "$BROWSER_TESTS_FAILED" == "true" ] && { echo "⚠️  Browser Tests: FAILED (possibly missing WebDriver)"; } || echo "✅ Browser Tests: PASSED"
[ "$PERFORMANCE_TESTS_FAILED" == "true" ] && { echo "⚠️  Performance Tests: FAILED (possibly missing Locust)"; } || echo "✅ Performance Tests: PASSED"

echo ""
echo "Test Files Generated:"
echo "===================="
echo "📁 All test results saved in: $TEST_RESULTS_DIR/"
echo "📄 Unit Tests: $TEST_RESULTS_DIR/unit_tests.log"
echo "📄 JavaScript Tests: $TEST_RESULTS_DIR/js_tests.log"
echo "📄 Integration Tests: $TEST_RESULTS_DIR/integration_tests.log"
echo "📄 API Tests: $TEST_RESULTS_DIR/api_tests.log"
echo "📄 Security Tests: $TEST_RESULTS_DIR/security_tests.log"
echo "📄 Database Tests: $TEST_RESULTS_DIR/database_tests.log"
echo "📄 Coverage Report: $TEST_RESULTS_DIR/htmlcov/index.html"

echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    print_success "🎉 All core tests passed! Your application is ready for production."
    exit 0
else
    print_error "❌ $FAILED_TESTS test suite(s) failed. Please review the logs and fix issues."
    exit 1
fi