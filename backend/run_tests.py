"""
Unit Test Runner Script
Run all unit tests for the DesignSensei chatbot

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py core              # Run core module tests
    python run_tests.py --verbose         # Run with verbose output
    python run_tests.py --coverage        # Run with coverage report
"""

import sys
import os
import django
from django.conf import settings
from django.test.utils import get_runner

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Setup Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

def run_tests():
    """Run the test suite"""
    TestRunner = get_runner(settings)
    
    # Parse command line arguments
    test_labels = []
    verbosity = 1
    
    if '--verbose' in sys.argv or '-v' in sys.argv:
        verbosity = 2
    
    if '--coverage' in sys.argv:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
        except ImportError:
            print("Coverage package not installed. Install with: pip install coverage")
            sys.exit(1)
    
    # Get test labels (app names or test modules)
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and not arg.startswith('-'):
            test_labels.append(arg)
    
    # If no labels specified, run all tests
    if not test_labels:
        test_labels = [
            'core.tests',
            'prompt_engine.tests',
        ]
    
    test_runner = TestRunner(verbosity=verbosity, interactive=True, keepdb=False)
    failures = test_runner.run_tests(test_labels)
    
    if '--coverage' in sys.argv:
        cov.stop()
        cov.save()
        print("\nCoverage Report:")
        cov.report()
        
        # Generate HTML coverage report
        print("\nGenerating HTML coverage report...")
        cov.html_report(directory='htmlcov')
        print("HTML report saved to htmlcov/index.html")
    
    sys.exit(bool(failures))

if __name__ == '__main__':
    print("=" * 70)
    print("DesignSensei Chatbot - Unit Test Suite")
    print("=" * 70)
    run_tests()
