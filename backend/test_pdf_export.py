#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scheduler.settings')
django.setup()

from scheduler_app.models import Timetable
from scheduler_app.utils import export_timetable_pdf

def test_pdf_export():
    try:
        # Get the first timetable
        timetable = Timetable.objects.first()
        if not timetable:
            print("No timetables found in database")
            return

        print(f"Testing PDF export for timetable: {timetable.name}")
        pdf_content = export_timetable_pdf(timetable)
        print(f"PDF export successful, content length: {len(pdf_content)} bytes")

        # Save to file for inspection
        with open('test_timetable.pdf', 'wb') as f:
            f.write(pdf_content)
        print("PDF saved to test_timetable.pdf")

    except Exception as e:
        print(f"PDF export failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_pdf_export()
