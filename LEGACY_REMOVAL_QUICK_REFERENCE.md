# Legacy Code Removal - Quick Reference

> **Critical Items for Immediate Action**

## 🔴 CRITICAL - Active Warnings in Logs

### **1. core/user_management.py**
**Problem**: Active legacy warnings appearing in logs
**Solution**: Remove legacy data access methods

```python
# REMOVE THESE METHODS:
get_user_data()           # Line 864 - Switch to core.user_data_handlers.get_user_data
save_user_data()          # Line 876 - Switch to core.user_data_handlers.save_user_data  
save_user_data_transaction() # Line 884 - Switch to core.user_data_handlers.save_user_data_transaction
```

**Action**: Find all callers and update to use `core.user_data_handlers`

---

### **2. core/validation.py**
**Problem**: Deprecated module still being imported
**Solution**: Remove entire file

```python
# REMOVE FILE: core/validation.py
# UPDATE ALL IMPORTS FROM:
from core.validation import *
# TO:
from core.user_data_validation import *
```

**Action**: Search for all imports of `core.validation` and update them

---

## 🟡 HIGH PRIORITY - UI Legacy Code

### **3. ui/dialogs/account_creator_dialog.py**
**Problem**: 5 legacy compatibility methods
**Solution**: Remove unused methods

```python
# REMOVE THESE METHODS:
on_category_changed()        # Line 347
on_service_changed()         # Line 362  
on_contact_info_changed()    # Line 377
on_task_group_toggled()      # Line 392
on_checkin_group_toggled()   # Line 407
```

**Action**: Verify no usage, then remove methods

---

### **4. ui/widgets/user_profile_settings_widget.py**
**Problem**: 5 legacy fallback blocks
**Solution**: Remove fallback code

```python
# REMOVE THESE FALLBACKS:
health_conditions fallback   # Line 393
medications fallback         # Line 407
allergies fallback           # Line 438
interests fallback           # Line 469
goals fallback               # Line 488
```

**Action**: Ensure dynamic list containers are used, then remove fallbacks

---

## 🟢 MEDIUM PRIORITY - Format Bridges

### **5. user/user_context.py**
**Problem**: Legacy format conversion methods
**Solution**: Remove format bridges

```python
# REMOVE THESE METHODS:
_load_legacy_format()        # Line 55
_save_legacy_format()        # Line 90
```

**Action**: Ensure new data structure is used everywhere, then remove bridges

---

## 📋 Removal Checklist

### **Before Each Removal:**
- [ ] Create backup
- [ ] Find all callers/imports
- [ ] Update callers to use modern methods
- [ ] Update tests
- [ ] Test functionality

### **After Each Removal:**
- [ ] Run tests
- [ ] Start system and verify
- [ ] Check logs for errors
- [ ] Update documentation

### **Final Verification:**
- [ ] Run legacy search script again
- [ ] Verify no legacy warnings in logs
- [ ] Run full test suite
- [ ] Test all major functionality

---

## 🎯 Recommended Order

1. **core/validation.py** - Easiest, just update imports
2. **core/user_management.py** - Most critical, active warnings
3. **ui/dialogs/account_creator_dialog.py** - UI methods
4. **ui/widgets/user_profile_settings_widget.py** - UI fallbacks
5. **user/user_context.py** - Format bridges
6. **Remaining items** - Scripts, documentation, etc.

---

## 🚨 Emergency Rollback

If something breaks:
1. **Git revert**: `git revert <commit>`
2. **Restore from backup**: Copy backup files back
3. **Check logs**: Identify what went wrong
4. **Fix incrementally**: Make smaller changes

---

## 📞 Quick Commands

```bash
# Find all imports of deprecated module
grep -r "from core.validation import" .

# Find all calls to legacy methods
grep -r "get_user_data\|save_user_data" .

# Run legacy search script
python scripts/search_legacy_compatibility.py

# Run tests
python run_tests.py

# Start system
python run_mhm.py
```
