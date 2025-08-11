#!/usr/bin/env python3
"""
Validation script for AIME Planner setup.
Checks that all dependencies and modules can be imported correctly.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def test_external_dependencies():
    """Test that all external dependencies can be imported."""
    print("🔍 Testing external dependencies...")

    dependencies = [
        "boto3",
        "openai",
        "sendgrid",
        "requests",
        "pydantic",
        "email_validator",
        "jinja2",
        "dateutil"
    ]

    failed = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"  ✅ {dep}")
        except ImportError as e:
            print(f"  ❌ {dep}: {e}")
            failed.append(dep)

    return len(failed) == 0

def test_project_modules():
    """Test that all project modules can be imported."""
    print("\n🔍 Testing project modules...")

    modules = [
        "models.conversation",
        "services.database",
        "services.email_service",
        "services.llm_service",
        "services.rails_api",
        "handlers.initiate_bid",
        "handlers.process_email"
    ]

    failed = []
    for module in modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            failed.append(module)

    return len(failed) == 0

def test_model_creation():
    """Test that models can be created successfully."""
    print("\n🔍 Testing model creation...")

    try:
        from models.conversation import Conversation, EventMetadata, VendorInfo, Question

        # Create test event metadata
        event_meta = EventMetadata(
            name="Test Event",
            dates=["2024-06-15"],
            event_type="test",
            planner_name="Test Planner",
            planner_email="test@example.com"
        )
        print("  ✅ EventMetadata creation")

        # Create test vendor info
        vendor_info = VendorInfo(
            name="Test Vendor",
            email="vendor@example.com",
            service_type="hotel"
        )
        print("  ✅ VendorInfo creation")

        # Create test questions
        questions = [
            Question(id=1, text="Test question?", required=True),
            Question(id=2, text="Another question?", required=False, options=["A", "B"])
        ]
        print("  ✅ Question creation")

        # Create conversation
        conversation = Conversation(
            event_metadata=event_meta,
            vendor_info=vendor_info,
            questions=questions
        )
        print("  ✅ Conversation creation")

        # Test methods
        unanswered = conversation.get_unanswered_required_questions()
        print(f"  ✅ Methods work (unanswered required: {len(unanswered)})")

        return True

    except Exception as e:
        print(f"  ❌ Model creation failed: {e}")
        return False

def test_service_initialization():
    """Test that services can be initialized (without AWS credentials)."""
    print("\n🔍 Testing service initialization...")

    # Set dummy environment variables
    os.environ.setdefault('OPENAI_API_KEY', 'test-key')
    os.environ.setdefault('SENDGRID_API_KEY', 'test-key')
    os.environ.setdefault('RAILS_API_BASE_URL', 'http://test.com')
    os.environ.setdefault('RAILS_API_KEY', 'test-key')
    os.environ.setdefault('CONVERSATION_TABLE_NAME', 'test-table')
    os.environ.setdefault('QUESTIONS_TABLE_NAME', 'test-table')

    services = [
        ("LLMService", "services.llm_service", "LLMService"),
        ("EmailService", "services.email_service", "EmailService"),
        ("RailsAPIService", "services.rails_api", "RailsAPIService")
    ]

    failed = []
    for name, module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            service_class = getattr(module, class_name)
            service = service_class()
            print(f"  ✅ {name}")
        except Exception as e:
            print(f"  ❌ {name}: {e}")
            failed.append(name)

    return len(failed) == 0

def main():
    """Run all validation tests."""
    print("🧪 AIME Planner Setup Validation")
    print("=" * 40)

    tests = [
        ("External Dependencies", test_external_dependencies),
        ("Project Modules", test_project_modules),
        ("Model Creation", test_model_creation),
        ("Service Initialization", test_service_initialization)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        if test_func():
            passed += 1
        print()

    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Setup is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
