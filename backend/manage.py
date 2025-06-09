#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    # client = OpenAI(api_key="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")

    # models = client.models.list()
    # for model in models.data:
    #     print(model.id)
    #     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)



if __name__ == '__main__':
    main()