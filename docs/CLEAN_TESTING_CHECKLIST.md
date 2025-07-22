# MHM Clean Manual Testing Checklist

> **Purpose**: Systematic manual testing of all dialogs and UI components  
> **Status**: Ready for testing  
> **Last Updated**: 2025-07-21

## 🎯 **Testing Strategy**

### **Order of Testing (Recommended)**
1. **Category Management Dialog** - Simplest, good starting point
2. **Channel Management Dialog** - Basic functionality
3. **Check-in Management Dialog** - Moderate complexity
4. **Task Management Dialog** - Moderate complexity
5. **Schedule Editor Dialog** - More complex
6. **User Profile Dialog** - Most complex, many fields
7. **Account Creator Dialog** - Most complex, integration testing

### **Before Starting**
- [ ] Run `python run_mhm.py` to ensure system starts
- [ ] Have a test user ready (or create one)
- [ ] Keep this checklist open for notes

---

## 📝 **1. Category Management Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Category Settings"
- [ ] Shows current user's selected categories
- [ ] Can check/uncheck categories
- [ ] Save button works and updates categories
- [ ] Cancel button works without saving changes
- [ ] Dialog closes properly after save/cancel

### **Data Persistence**
- [ ] Categories save correctly to user preferences
- [ ] Categories load correctly when reopening dialog
- [ ] Changes persist after closing and reopening main app

### **Edge Cases**
- [ ] What happens with no categories selected? (should show warning)
- [ ] What happens if user has no categories configured?
- [ ] What happens if user data is corrupted/missing?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **2. Channel Management Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Channel Settings"
- [ ] Shows current user's channel configuration
- [ ] Can select different communication channels (Discord, Email, Telegram)
- [ ] Can enter/update contact information
- [ ] Save button works and updates channel settings
- [ ] Cancel button works without saving changes

### **Data Persistence**
- [ ] Channel settings save correctly to user preferences
- [ ] Channel settings load correctly when reopening dialog
- [ ] Contact information persists correctly

### **Validation**
- [ ] Shows validation error for invalid email format
- [ ] Shows validation error for invalid Discord format
- [ ] Shows validation error for invalid Telegram format
- [ ] Prevents saving with invalid contact information

### **Edge Cases**
- [ ] What happens if no channel is selected?
- [ ] What happens if contact info is empty?
- [ ] What happens if user has no channel configured?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **3. Check-in Management Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Check-in Settings"
- [ ] Shows current user's check-in configuration
- [ ] Can enable/disable check-ins
- [ ] Can add new time periods
- [ ] Can edit existing time periods
- [ ] Can delete time periods
- [ ] Can undo deleted time periods
- [ ] Save button works and updates settings

### **Time Period Management**
- [ ] Time periods save correctly
- [ ] Time periods load correctly when reopening
- [ ] Period names are preserved (not converted to title case)
- [ ] Can set start and end times
- [ ] Can enable/disable individual periods

### **Data Persistence**
- [ ] Check-in settings save correctly to user preferences
- [ ] Time periods save correctly to user schedules
- [ ] Changes persist after closing and reopening main app

### **Edge Cases**
- [ ] What happens with no time periods?
- [ ] What happens if all periods are disabled?
- [ ] What happens if time periods overlap?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **4. Task Management Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Task Management"
- [ ] Shows current user's task configuration
- [ ] Can enable/disable task management
- [ ] Can add new time periods
- [ ] Can edit existing time periods
- [ ] Can delete time periods
- [ ] Can undo deleted time periods
- [ ] Task statistics display correctly
- [ ] Save button works and updates settings

### **Time Period Management**
- [ ] Time periods save correctly
- [ ] Time periods load correctly when reopening
- [ ] Period names are preserved (not converted to title case)
- [ ] Can set start and end times
- [ ] Can enable/disable individual periods

### **Data Persistence**
- [ ] Task settings save correctly to user preferences
- [ ] Time periods save correctly to user schedules
- [ ] Changes persist after closing and reopening main app

### **Edge Cases**
- [ ] What happens with no time periods?
- [ ] What happens if all periods are disabled?
- [ ] What happens if time periods overlap?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **5. Schedule Editor Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Schedule Editor"
- [ ] Shows current user's schedule for selected category
- [ ] Can add new time periods
- [ ] Can edit existing time periods
- [ ] Can delete time periods
- [ ] Can undo deleted time periods
- [ ] Can enable/disable periods
- [ ] Save button works and updates schedule

### **Time Period Management**
- [ ] Time periods save correctly
- [ ] Time periods load correctly when reopening
- [ ] Period names are preserved (not converted to title case)
- [ ] Can set start and end times with AM/PM
- [ ] Can set days of the week
- [ ] Can enable/disable individual periods

### **Data Persistence**
- [ ] Schedule changes save correctly to user schedules
- [ ] Changes persist after closing and reopening main app
- [ ] Schedule data doesn't overwrite "ALL" time period

### **Edge Cases**
- [ ] What happens with no time periods?
- [ ] What happens if all periods are disabled?
- [ ] What happens if time periods overlap?
- [ ] What happens with the "ALL" time period?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **6. User Profile Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Personalization"
- [ ] Shows current user's profile information
- [ ] All fields are present and functional:
  - [ ] Preferred name
  - [ ] Gender identity
  - [ ] Date of birth
  - [ ] Health conditions
  - [ ] Medications
  - [ ] Allergies
  - [ ] Interests
  - [ ] Goals
  - [ ] Loved ones
  - [ ] Notes for AI
  - [ ] Timezone
- [ ] Save button works and updates profile
- [ ] Cancel button works without saving changes

### **Data Persistence**
- [ ] All fields save correctly to user context
- [ ] All fields load correctly when reopening dialog
- [ ] Date of birth saves and loads properly
- [ ] Timezone saves to account.json (not user_context.json)
- [ ] Changes persist after closing and reopening main app

### **Field Functionality**
- [ ] Can enter text in all text fields
- [ ] Can add/remove items in list fields (health, meds, allergies, interests, goals)
- [ ] Date picker works for date of birth
- [ ] Timezone dropdown works
- [ ] Loved ones field handles complex data (name - type - relationships)

### **Validation**
- [ ] Date of birth validation works (invalid dates show error)
- [ ] All fields are optional (no validation errors for empty fields)
- [ ] Type checking works for all fields

### **Edge Cases**
- [ ] What happens with very long text entries?
- [ ] What happens with special characters?
- [ ] What happens if user_context.json is corrupted?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 📝 **7. Account Creator Dialog**

### **Basic Functionality**
- [ ] Opens without errors when clicking "Create New Account"
- [ ] All tabs are present: Basic Information, Messages, Tasks, Check-ins
- [ ] Can enter username and select timezone
- [ ] Feature enablement checkboxes work
- [ ] Tabs appear/disappear based on feature selection
- [ ] Save button works and creates user
- [ ] Cancel button works without creating user

### **Tab Functionality**
- [ ] **Basic Information Tab**:
  - [ ] Username field works
  - [ ] Timezone dropdown works
  - [ ] Feature checkboxes work (messages, tasks, check-ins)
- [ ] **Messages Tab** (when enabled):
  - [ ] Communication service selection works
  - [ ] Contact information field works
  - [ ] Message category selection works
- [ ] **Tasks Tab** (when enabled):
  - [ ] Task settings configuration works
  - [ ] Time period management works
- [ ] **Check-ins Tab** (when enabled):
  - [ ] Check-in settings configuration works
  - [ ] Time period management works

### **Integration**
- [ ] "Setup Profile" button opens user profile dialog
- [ ] User profile dialog receives correct data
- [ ] Created user appears in main admin panel dropdown
- [ ] All user data files are created correctly

### **Validation**
- [ ] Username is required
- [ ] At least one feature must be enabled
- [ ] If messages enabled: communication service and contact info required
- [ ] If messages enabled: at least one category must be selected
- [ ] Validation errors show but don't close dialog
- [ ] Can fix validation errors and retry save

### **Data Persistence**
- [ ] All entered data saves correctly
- [ ] All selections save correctly
- [ ] User account file created with correct data
- [ ] User preferences file created with correct data
- [ ] User schedules file created with correct data
- [ ] User context file created with correct data

### **Edge Cases**
- [ ] What happens with duplicate usernames?
- [ ] What happens with invalid contact information?
- [ ] What happens if no features are enabled?

**Notes:**
```
Test Date: ________
Tester: ________
Issues Found: ________
```

---

## 🚨 **Critical Issues to Watch For**

### **High Priority**
- [ ] **Data Loss**: Users created but selections/entered information missing
- [ ] **Validation Dialog Closes Account Creation**: Validation errors close dialog instead of allowing fix
- [ ] **Missing Validation**: No duplicate username checks, format validation

### **Medium Priority**
- [ ] **UI Responsiveness**: Dialogs slow to open/close
- [ ] **Data Corruption**: Files not saving correctly
- [ ] **Integration Issues**: Dialogs don't communicate with main window

### **Low Priority**
- [ ] **Visual Issues**: Layout problems, missing elements
- [ ] **Minor Bugs**: Non-critical functionality issues

---

## 📋 **Testing Summary**

### **Overall Results**
- [ ] All dialogs open without errors
- [ ] All dialogs save data correctly
- [ ] All dialogs load data correctly
- [ ] All validation works properly
- [ ] All integration works properly

### **Issues Found**
```
Critical Issues: ________
High Priority Issues: ________
Medium Priority Issues: ________
Low Priority Issues: ________
```

### **Next Steps**
- [ ] Fix critical issues first
- [ ] Address high priority issues
- [ ] Document all findings
- [ ] Update TODO.md with results
- [ ] Plan fixes for identified issues

---

**Remember**: Test one dialog at a time, document everything, and don't rush through the testing! 