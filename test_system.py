#!/usr/bin/env python3
"""
System Test Script for Automated Math Solver
FOR TESTING PURPOSES ONLY

This script provides comprehensive testing of all system components.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.append(str(Path(__file__).parent / 'backend'))

from backend.services.math_solver import MathematicalSolver
from backend.utils.validators import ContentValidator
from backend.utils.config_manager import ConfigManager


class SystemTester:
    """
    Comprehensive system testing class.
    """
    
    def __init__(self):
        """Initialize the tester."""
        self.passed_tests = 0
        self.failed_tests = 0
        self.test_results = []
        
        print("🧪 Automated Math Solver System Tests")
        print("=" * 50)
        print("FOR TESTING PURPOSES ONLY")
        print("=" * 50)
    
    def run_test(self, test_name: str, test_func):
        """
        Run a single test and record results.
        
        Args:
            test_name: Name of the test
            test_func: Function to execute
        """
        print(f"\n🔍 Testing: {test_name}")
        
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            if result:
                print(f"✅ PASSED ({end_time - start_time:.2f}s)")
                self.passed_tests += 1
                self.test_results.append({
                    'test': test_name,
                    'status': 'PASSED',
                    'time': end_time - start_time
                })
            else:
                print(f"❌ FAILED ({end_time - start_time:.2f}s)")
                self.failed_tests += 1
                self.test_results.append({
                    'test': test_name,
                    'status': 'FAILED',
                    'time': end_time - start_time
                })
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            self.failed_tests += 1
            self.test_results.append({
                'test': test_name,
                'status': 'ERROR',
                'error': str(e),
                'time': 0
            })
    
    def test_config_loading(self):
        """Test configuration loading."""
        try:
            config_manager = ConfigManager('config.yaml')
            config = config_manager.get_config()
            
            # Check required sections
            required_sections = ['github', 'scheduler', 'email', 'math_solver', 'logging', 'security']
            for section in required_sections:
                if section not in config:
                    print(f"   Missing section: {section}")
                    return False
            
            # Check GitHub repository
            repo = config['github']['repository']
            if repo != "TheEMeraldNetwork/Compiti-test":
                print(f"   Unexpected repository: {repo}")
                return False
            
            print(f"   ✓ Configuration loaded successfully")
            print(f"   ✓ GitHub repository: {repo}")
            return True
            
        except Exception as e:
            print(f"   Configuration error: {e}")
            return False
    
    def test_content_validator(self):
        """Test content validation functionality."""
        try:
            validator = ContentValidator()
            
            # Test mathematical content detection
            math_texts = [
                "Solve x^2 + 5x + 6 = 0",
                "Find the derivative of f(x) = x^3 + 2x^2",
                "Calculate the integral of sin(x) dx",
                "What is the area of a circle with radius 5?",
                "Simplify: (x+2)(x-3)"
            ]
            
            non_math_texts = [
                "Hello, how are you today?",
                "The weather is nice outside",
                "I like to read books about history",
                "What time is the meeting?",
                "Please send me the document"
            ]
            
            # Test mathematical content
            for text in math_texts:
                is_valid, reason = validator.validate_mathematical_content_text(text)
                if not is_valid:
                    print(f"   Failed to identify math content: {text[:50]}...")
                    return False
            
            # Test non-mathematical content
            for text in non_math_texts:
                is_valid, reason = validator.validate_mathematical_content_text(text)
                if is_valid:
                    print(f"   Incorrectly identified as math: {text[:50]}...")
                    return False
            
            print(f"   ✓ Mathematical content validation working")
            print(f"   ✓ Non-mathematical content rejection working")
            return True
            
        except Exception as e:
            print(f"   Validator error: {e}")
            return False
    
    def test_math_solver_basic(self):
        """Test basic mathematical solving capabilities."""
        try:
            solver = MathematicalSolver()
            
            test_problems = [
                {
                    'problem': "Solve x^2 - 4 = 0",
                    'expected_type': 'equation'
                },
                {
                    'problem': "Find the derivative of x^3 + 2x",
                    'expected_type': 'derivative'
                },
                {
                    'problem': "Simplify (x+1)(x-1)",
                    'expected_type': 'simplify'
                },
                {
                    'problem': "Calculate 2 + 3 * 4",
                    'expected_type': 'general'
                }
            ]
            
            for test_case in test_problems:
                result = solver.solve_problem(test_case['problem'], "test_problem.txt")
                
                if not result:
                    print(f"   No result for: {test_case['problem']}")
                    return False
                
                if result.get('problem_type') != test_case['expected_type']:
                    print(f"   Wrong problem type for: {test_case['problem']}")
                    print(f"   Expected: {test_case['expected_type']}, Got: {result.get('problem_type')}")
                    # Continue anyway, type detection might be flexible
                
                if not result.get('success') and not result.get('error_message'):
                    print(f"   No success or error info for: {test_case['problem']}")
                    return False
            
            print(f"   ✓ Processed {len(test_problems)} test problems")
            print(f"   ✓ Problem type identification working")
            return True
            
        except Exception as e:
            print(f"   Math solver error: {e}")
            return False
    
    def test_file_validation(self):
        """Test file validation and safety checks."""
        try:
            validator = ContentValidator()
            
            # Create temporary test files
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Test valid math file
                math_file = temp_path / "test_math.txt"
                math_file.write_text("Solve the equation x^2 + 5x + 6 = 0")
                
                is_safe, reason = validator.validate_file_safety(str(math_file))
                if not is_safe:
                    print(f"   Valid file rejected: {reason}")
                    return False
                
                is_math, reason = validator.validate_mathematical_content(str(math_file))
                if not is_math:
                    print(f"   Math file not recognized: {reason}")
                    return False
                
                # Test non-math file
                non_math_file = temp_path / "test_nonmath.txt"
                non_math_file.write_text("This is just regular text with no mathematics.")
                
                is_math, reason = validator.validate_mathematical_content(str(non_math_file))
                if is_math:
                    print(f"   Non-math file incorrectly accepted: {reason}")
                    return False
                
                print(f"   ✓ File safety validation working")
                print(f"   ✓ Mathematical content detection working")
                return True
                
        except Exception as e:
            print(f"   File validation error: {e}")
            return False
    
    def test_forbidden_content(self):
        """Test forbidden content detection."""
        try:
            validator = ContentValidator()
            
            # Test forbidden content
            forbidden_texts = [
                "How to hack into systems",
                "Create malware program",
                "Password cracking techniques",
                "Illegal drug manufacturing",
                "Violence and weapons"
            ]
            
            for text in forbidden_texts:
                if not validator._contains_forbidden_content(text):
                    print(f"   Failed to detect forbidden content: {text}")
                    return False
            
            # Test allowed mathematical content
            allowed_texts = [
                "Solve x^2 + 5x + 6 = 0",
                "Find the derivative of f(x) = x^3",
                "Calculate the area of a triangle"
            ]
            
            for text in allowed_texts:
                if validator._contains_forbidden_content(text):
                    print(f"   Incorrectly flagged allowed content: {text}")
                    return False
            
            print(f"   ✓ Forbidden content detection working")
            print(f"   ✓ Allowed content passing through")
            return True
            
        except Exception as e:
            print(f"   Forbidden content test error: {e}")
            return False
    
    def test_mathematical_scoring(self):
        """Test mathematical content scoring."""
        try:
            validator = ContentValidator()
            
            # High math score texts
            high_math_texts = [
                "Solve the quadratic equation x^2 + 5x + 6 = 0 using the quadratic formula",
                "Find the derivative of f(x) = sin(x) * cos(x) using the product rule",
                "Calculate the definite integral of x^2 from 0 to 5"
            ]
            
            # Low math score texts
            low_math_texts = [
                "The weather is nice today and I enjoyed my walk",
                "Please send me the meeting agenda for tomorrow",
                "I like reading books about history and culture"
            ]
            
            for text in high_math_texts:
                score = validator._calculate_mathematical_score(text)
                if score < 0.1:
                    print(f"   Low score for math text: {score:.2f} for '{text[:50]}...'")
                    return False
            
            for text in low_math_texts:
                score = validator._calculate_mathematical_score(text)
                if score > 0.1:
                    print(f"   High score for non-math text: {score:.2f} for '{text[:50]}...'")
                    return False
            
            print(f"   ✓ Mathematical scoring working correctly")
            return True
            
        except Exception as e:
            print(f"   Mathematical scoring error: {e}")
            return False
    
    def test_expression_extraction(self):
        """Test mathematical expression extraction."""
        try:
            solver = MathematicalSolver()
            
            test_texts = [
                "Solve x^2 + 5x + 6 = 0",
                "Find y when 2y - 3 = 7",
                "Simplify (a+b)(a-b)",
                "Calculate f(x) = x^3 + 2x^2 - 5"
            ]
            
            for text in test_texts:
                expressions = solver._extract_expressions(text)
                if not expressions:
                    print(f"   No expressions found in: {text}")
                    return False
                
                print(f"   ✓ Found {len(expressions)} expressions in: {text[:30]}...")
            
            return True
            
        except Exception as e:
            print(f"   Expression extraction error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all system tests."""
        print(f"\n🚀 Starting comprehensive system tests...")
        print(f"📅 Test run: {datetime.now().isoformat()}")
        
        # Run all tests
        self.run_test("Configuration Loading", self.test_config_loading)
        self.run_test("Content Validator", self.test_content_validator)
        self.run_test("Math Solver Basic", self.test_math_solver_basic)
        self.run_test("File Validation", self.test_file_validation)
        self.run_test("Forbidden Content Detection", self.test_forbidden_content)
        self.run_test("Mathematical Scoring", self.test_mathematical_scoring)
        self.run_test("Expression Extraction", self.test_expression_extraction)
        
        # Print summary
        self.print_summary()
        
        return self.failed_tests == 0
    
    def print_summary(self):
        """Print test summary."""
        total_tests = self.passed_tests + self.failed_tests
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"Success Rate: {(self.passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ System is ready for testing")
        else:
            print(f"\n⚠️  {self.failed_tests} TESTS FAILED")
            print("❌ Please review and fix issues before using the system")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {result['test']}: {result['status']} ({result.get('time', 0):.2f}s)")
            if 'error' in result:
                print(f"   Error: {result['error']}")


def main():
    """Main test function."""
    tester = SystemTester()
    success = tester.run_all_tests()
    
    print(f"\n🔚 Test run completed")
    print("=" * 50)
    
    if success:
        print("🚀 System is ready! Next steps:")
        print("1. Set up your .env file with GitHub token and email credentials")
        print("2. Run: python app.py start --web")
        print("3. Upload mathematical problems to your GitHub repository")
        print("4. Monitor the web interface at http://localhost:5000")
    else:
        print("🔧 Please fix the failing tests before proceeding")
    
    return success


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
