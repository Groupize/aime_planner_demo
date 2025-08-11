#!/usr/bin/env python3
"""
Quick script to fix the most common flake8 issues.
"""

import os
import re

def fix_unused_imports():
    """Fix unused imports in test files."""

    files_to_fix = [
        'tests/unit/handlers/test_process_email.py',
        'tests/unit/models/test_conversation.py',
        'tests/unit/services/test_database.py',
        'tests/unit/services/test_email_service.py',
        'tests/unit/services/test_llm_service.py',
        'tests/unit/services/test_rails_api.py'
    ]

    for file_path in files_to_fix:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()

            # Remove common unused imports
            content = content.replace('import pytest\n', '')
            content = content.replace('from unittest.mock import MagicMock', 'from unittest.mock import Mock, patch')
            content = content.replace('from unittest.mock import Mock, patch, MagicMock', 'from unittest.mock import Mock, patch')
            content = content.replace('import re\n', '')
            content = content.replace('from datetime import datetime\n', '')
            content = re.sub(r'from models\.conversation import.*ConversationStatus.*\n', '', content)
            content = re.sub(r'from models\.conversation import.*Question.*\n', '', content)

            # Fix specific issues
            if 'test_rails_api.py' in file_path:
                content = re.sub(r'datetime = Mock.*\n', '', content)
                content = content.replace("'response' is assigned to but never used", "# response unused")
                content = content.replace("'rails_api' is assigned to but never used", "# rails_api unused")

            with open(file_path, 'w') as f:
                f.write(content)

            print(f"Fixed imports in {file_path}")

if __name__ == '__main__':
    fix_unused_imports()
