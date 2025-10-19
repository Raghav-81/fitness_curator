# 🏋️ Workout Creator - User Guide

## Overview

The Workout Creator is a professional tool for trainers to create, manage, and share customized workout plans with their clients. It features a modern, intuitive interface with drag-and-drop functionality and real-time video preview.

---

## ✨ Features

### 1. **Client Management**
- Create and manage client profiles
- Store client information (name, email, phone, age, goals)
- Add trainer notes for each client

### 2. **Workout Plan Builder**
- **Split-view interface**: Form on left, video library on right
- **Dynamic exercise table**: Add, remove, and reorder exercises
- **Drag-and-drop**: Easily add videos from library to workout plan
- **Day organization**: Choose between day numbers (Day 1, Day 2) or days of week (Monday, Tuesday)
- **Exercise details**: Sets, reps, and custom notes for each exercise
- **Template support**: Save plans as reusable templates

### 3. **Video Library Integration**
- **Search functionality**: Find videos by name or description
- **Category filtering**: Filter by workout category
- **Video preview**: Click to preview any video before adding
- **Collapsible panel**: Toggle video library visibility

### 4. **Shareable Links**
- **Unique URLs**: Each plan gets a unique shareable link
- **Client access**: Clients can view their workout plan via the link
- **Easy sharing**: Copy link with one click

### 5. **Professional UI/UX**
- **Smooth animations**: Powered by Animate.css
- **Modern design**: Clean, gradient-based interface
- **Responsive**: Works on desktop and tablet
- **Toast notifications**: Real-time feedback for all actions

---

## 🚀 How to Use

### Step 1: Access Workout Creator

1. Start the application:
   ```bash
   cd /home/streamoid/Desktop/Raghav/Personal/fitness_curator
   python run.py
   ```

2. Open browser and navigate to: `http://localhost:8000`

3. Click on the **"Workout Creator"** tab in the navigation

### Step 2: Select or Create a Client

1. **Select existing client**: Choose from the dropdown
2. **Create new client**: Click "New Client" button (coming soon in UI)
3. **Via API**: Use the test script to create clients programmatically

### Step 3: Fill Plan Details

1. **Plan Name**: Give your workout plan a descriptive name
   - Example: "4-Week Strength Building Program"

2. **Description**: Describe the plan's goals and approach
   - Example: "Progressive overload focusing on compound movements"

3. **Dates**: Set start and end dates (optional)

4. **Day Format**: Choose between:
   - **Day Numbers**: Day 1, Day 2, Day 3...
   - **Days of Week**: Monday, Tuesday, Wednesday...

5. **Save as Template**: Check this to reuse the plan for other clients

### Step 4: Add Exercises

#### Method 1: From Video Library
1. Search or browse videos in the right panel
2. Click on a video to add it to the workout plan
3. Video automatically appears in the exercise table

#### Method 2: Manual Entry
1. Click "Add Exercise" button
2. Select video from the exercise row
3. Fill in sets, reps, and notes

#### Configure Exercise Details:
- **Day**: Select which day this exercise belongs to
- **Sets**: Number of sets (e.g., 3)
- **Reps**: Number of reps (e.g., "10" or "10-12" or "AMRAP")
- **Notes**: Any special instructions or modifications

### Step 5: Organize Exercises

- **Drag to reorder**: Use the grip handle (⋮⋮) to drag exercises
- **Remove exercise**: Click the ✕ button
- **Preview video**: Click the play icon to watch the video

### Step 6: Save and Share

1. Click **"Save Workout Plan"** button
2. Wait for success confirmation
3. **Copy the shareable link** from the modal
4. Send link to your client via email/SMS

---

## 📊 API Endpoints

### Clients

```bash
# Create a client
POST /api/clients
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "+1234567890",
  "age": 30,
  "goals": "Build muscle",
  "trainer_notes": "Beginner level"
}

# Get all clients
GET /api/clients

# Get specific client
GET /api/clients/{client_id}

# Update client
PUT /api/clients/{client_id}

# Delete client
DELETE /api/clients/{client_id}
```

### Workout Plans

```bash
# Create workout plan
POST /api/workout-plans
{
  "client_id": 1,
  "plan_name": "Strength Program",
  "description": "4-week program",
  "start_date": "2025-01-01T00:00:00",
  "end_date": "2025-01-28T00:00:00",
  "is_template": false,
  "day_type": "day_number",
  "exercises": [
    {
      "video_id": 1,
      "day": "1",
      "sets": 3,
      "reps": "10",
      "notes": "Focus on form",
      "order_index": 0
    }
  ]
}

# Get all plans
GET /api/workout-plans

# Get plans for specific client
GET /api/workout-plans?client_id=1

# Get templates only
GET /api/workout-plans?is_template=true

# Get specific plan
GET /api/workout-plans/{plan_id}

# Get plan by share token (for clients)
GET /api/workout-plans/share/{share_token}

# Update plan
PUT /api/workout-plans/{plan_id}

# Delete plan
DELETE /api/workout-plans/{plan_id}
```

### Exercises

```bash
# Add exercise to plan
POST /api/workout-plans/{plan_id}/exercises

# Update exercise
PUT /api/exercises/{exercise_id}

# Delete exercise
DELETE /api/exercises/{exercise_id}

# Update tracking (for client use)
PATCH /api/exercises/{exercise_id}/tracking
{
  "completed": true,
  "weight_logged": [135, 135, 140]
}
```

---

## 🧪 Testing

### Quick Test Script

Run the included test script to verify everything works:

```bash
cd /home/streamoid/Desktop/Raghav/Personal/fitness_curator
python test_workout_creator.py
```

This will:
1. Create a test client
2. Fetch video IDs
3. Create a sample workout plan
4. Display the shareable link

### Manual Testing Checklist

- [ ] Navigate to Workout Creator tab
- [ ] Select a client from dropdown
- [ ] Enter plan details
- [ ] Search for videos in library
- [ ] Click video to add to plan
- [ ] Fill in sets/reps/notes
- [ ] Drag to reorder exercises
- [ ] Remove an exercise
- [ ] Preview a video
- [ ] Save the plan
- [ ] Copy shareable link
- [ ] Reset the form

---

## 🎨 UI Components

### Navigation
- **Sticky header**: Always visible while scrolling
- **Tab switching**: Smooth transitions between sections
- **Active indicators**: Clear visual feedback

### Form Panel (Left)
- **Sectioned layout**: Organized by Client Info, Plan Details, Exercises
- **Animated sections**: Staggered fade-in animations
- **Validation**: Required fields marked with *

### Video Library (Right)
- **Collapsible panel**: Toggle visibility with button
- **Search bar**: Real-time filtering
- **Category dropdown**: Quick filtering
- **Video cards**: Hover effects and selection states

### Exercise Table
- **Sortable rows**: Drag-and-drop reordering
- **Inline editing**: Edit directly in table cells
- **Video preview**: Click play icon to watch
- **Remove button**: Animated deletion

---

## 🔧 Technical Details

### Database Schema

**clients table:**
- id, name, email, phone, age, goals, trainer_notes
- created_at, updated_at

**workout_plans table:**
- id, client_id, plan_name, description
- start_date, end_date, is_template, day_type
- share_token (unique, for shareable links)
- created_at, updated_at

**plan_exercises table:**
- id, plan_id, video_id, day
- sets, reps, notes, order_index
- completed, weight_logged (for client tracking)
- created_at

### Technologies Used

**Backend:**
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite

**Frontend:**
- Vanilla JavaScript
- Animate.css (animations)
- SortableJS (drag-and-drop)
- Font Awesome (icons)
- Custom CSS with gradients

### File Structure

```
fitness_curator/
├── app/
│   ├── models.py              # Database models
│   ├── workout_api.py         # API endpoints
│   ├── main.py                # Main app (updated)
│   └── database.py            # Database utilities
├── static/
│   ├── css/
│   │   └── workout-creator.css
│   └── js/
│       └── workout-creator.js
├── templates/
│   └── index.html             # Main page (updated)
└── test_workout_creator.py    # Test script
```

---

## 🚧 Future Enhancements

### Phase 2 (Coming Soon):
- [ ] Client portal for viewing plans
- [ ] Exercise completion tracking
- [ ] Weight logging per set
- [ ] Progress charts and analytics
- [ ] Exercise substitution suggestions
- [ ] Rest timer between sets
- [ ] Workout history
- [ ] Export to PDF
- [ ] Mobile app integration

### Phase 3 (Planned):
- [ ] Video upload functionality
- [ ] Custom exercise creation
- [ ] Nutrition planning integration
- [ ] Progress photos
- [ ] Client messaging
- [ ] Calendar view
- [ ] Recurring workout schedules
- [ ] Team/group workouts

---

## 📝 Best Practices

### For Trainers:

1. **Be Descriptive**: Use clear plan names and detailed notes
2. **Organize by Days**: Group exercises logically by training days
3. **Progressive Overload**: Adjust sets/reps over time
4. **Video Selection**: Choose videos that match client's skill level
5. **Save Templates**: Create templates for common programs
6. **Client Communication**: Share links via preferred method

### For Development:

1. **Modular Code**: Each feature in separate files
2. **API First**: All functionality accessible via API
3. **Error Handling**: Graceful degradation
4. **Responsive Design**: Mobile-friendly layouts
5. **Performance**: Lazy loading and caching
6. **Security**: Validate all inputs, sanitize data

---

## 🐛 Troubleshooting

### Issue: Client dropdown is empty
**Solution**: Create clients via API or test script first

### Issue: Videos not loading in library
**Solution**: Ensure video database is populated (189 videos should exist)

### Issue: Drag-and-drop not working
**Solution**: Check that SortableJS library is loaded

### Issue: Save button not responding
**Solution**: Check browser console for errors, ensure all required fields are filled

### Issue: Shareable link not working
**Solution**: Verify share_token is generated and plan exists in database

---

## 📞 Support

For issues or questions:
1. Check browser console for errors
2. Review API documentation at `/docs`
3. Run test script to verify backend
4. Check database tables are created

---

**Version**: 1.0.0  
**Last Updated**: October 19, 2025  
**Status**: ✅ Production Ready
