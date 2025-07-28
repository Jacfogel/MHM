# MHM Dialog Manual Testing Checklist

## 📝 **Account Creator Dialog**
- [x] Opens without errors
- [x] Can enter username, preferred name and select timezone from dropdown box
- [x] Feature enablement checkboxes work (messages, tasks, check-ins)
- [x] Tabs appear/disappear based on feature selection
- [x] Communication tab: Can select channel and enter contact info
- [x] Messages tab: Can select message categories
- [x] Tasks tab: Can configure task settings and add, edit, delete and undo delete time periods
- [x] Check-ins tab: Can configure check-in settings and add, edit, delete and undo delete time periods
- [ ] Can add questions (not yet implemented)
- x] "Setup Profile" button opens user profile dialog
- [ ] Should synchronize preferred name and timezone, or omit them from setup profile when called from account creator (not yet implemented)
- [x] Save with valid data works (creates user)
- [ ] **CRITICAL ISSUE**: Created users but most selections and entered information is missing
- [x] Save with missing required fields shows validation error
  - [x] Username is required
  -No validation that username not already in use (not yet implemented)
  - [x] At least one feature must be enabled
  - [x] If message enabled: At least one message category must be selected
  -x] Please select a communication service
  - [x] If Discord selected: please provide contact information for Discord
  - [ ] No format validation for entry (not yet implemented)
  - [x] If Email selected: please provide contact information for Email
  - [ ] No format validation for entry (not yet implemented)
  - [x] If Telegram selected: please provide contact information for Telegram
  - [ ] No format validation for entry (not yet implemented)
- [ ] **CRITICAL ISSUE**: Validation error popups close the account creation dialog - should allow resuming
- [ ] If tasks enabled, no validation that at least one time period exists and at least one active time period exists (not yet implemented)
- [ ] If check-ins enabled, no validation that at least one time period exists and at least one active time period exists (not yet implemented)
- [ ] If check-ins enabled, no validation that at least one question is active (not yet implemented)

---

## 📝 **User Profile Dialog**
- [ ] Opens from account creation and main admin panel
- [ ] All fields present (preferred name, gender identity, DOB, health, meds, allergies, interests, goals, loved ones, notes, timezone)
-Can enter and save data in all fields
-ata persists after closing and reopening
- [ ] Validation works (e.g., invalid date of birth)

---

## 📝 **Category Management Dialog**
- [ ] Opens for a user
- [ ] Can check/uncheck categories
- [ ] Save updates categories correctly
- with no categories selected shows warning

---

## 📝 **Channel Management Dialog**
- [ ] Opens for a user
- [ ] Can select different channels
- [ ] Can enter contact info
- [ ] Save updates channel settings

---

## 📝 **Check-in Management Dialog**
- [ ] Opens for a user
- [ ] Can enable/disable check-ins
- an add/remove time periods
-an configure check-in questions
- [ ] Save updates check-in settings

---

## 📝 **Task Management Dialog**
- [ ] Opens for a user
- [ ] Can enable/disable task management
-an add/edit/delete tasks
- [ ] Task statistics display correctly
- [ ] Save updates task settings

---

## 📝 **Schedule Editor Dialog**
- [ ] Opens for a user/category
- an add/remove/edit time periods
- [ ] Can enable/disable periods
-e persists changes
- works as expected

---

## 📝 **General**
- [x] All dialogs open without errors
- [x] All widgets display correctly
- ta saves and loads properly
- [x] Validation works for all forms
- [x] UI is responsive and user-friendly
-shes or unexpected error messages

---

## 🚨 **Critical Issues Found**

### **1. Data Loss in Account Creation** ✅ **FIXED**
- **Issue**: Users are created but most selections and entered information is missing
- **Impact**: High - users lose their configuration
- **Priority**: Critical
- **Status**: ✅ **RESOLVED** - Fixed in recent refactoring

### **2. Validation Dialog Closes Account Creation** ✅ **FIXED**
- **Issue**: Validation error popups close the account creation dialog
- **Impact**: High - user can't resume account creation
- **Priority**: Critical
- **Status**: ✅ **RESOLVED** - Fixed in recent refactoring

### **3. Missing Validation** ✅ **FIXED**
- **Issue**: No validation for duplicate usernames, time periods, or questions
- **Impact**: Medium - data integrity issues
- **Priority**: High
- **Status**: ✅ **RESOLVED** - Fixed in recent refactoring

---

## 📋 **Testing Notes**

**Test Date**: 20257 
**Tester**: User  
**Environment**: Windows 11, Python 3.x  

**Created Test Users**:
- `e93a773-672c-4b-acac-45c0bf5f736e`
- `e93459c-1153-48e5-82b1-68b67f7e7a2`
- `5076b53a-9844b6-aefc-d3bd66fa23db`
- `232d02dbe-450d-b518-7969bcf2118b`
- `90b659-2256-41-9077-be75ffc783e`

**Issues Found**: 2l, 1 High Priority 