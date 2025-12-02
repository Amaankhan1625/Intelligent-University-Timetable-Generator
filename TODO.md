# Timetable Editing Feature Implementation

## Frontend Changes
- [ ] Update `components/TimetableGrid.tsx` to enable actual drag-and-drop editing
- [ ] Add conflict checking and popup display in TimetableGrid
- [ ] Update `app/dashboard/timetables/[id]/page.tsx` to add edit mode toggle

## Backend Changes
- [ ] Add `update_slot` endpoint in `backend/scheduler_app/views.py` TimetableViewSet
- [ ] Implement conflict checking logic in views.py
- [ ] Add utility function in `backend/scheduler_app/utils.py` for instructor conflicts

## Testing
- [x] Test edit functionality with conflict scenarios
- [x] Ensure UI updates correctly after successful edits
- [x] Debug and fix drag-and-drop recognition issues
