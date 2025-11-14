# Critical Fixes Applied to Module Wrappers

## Issues Found and Fixed

### 1. ❌ Sparkle Directory Path Inconsistency
**File:** `cli/modules/common/clean.py`
- **Wrong:** `chromium_path.parent.parent/Sparkle`
- **Correct:** `chromium_path/third_party/sparkle`
- **Impact:** Clean would look for Sparkle in wrong location, never cleaning it

### 2. ❌ macOS Signing Environment Variables
**File:** `cli/modules/setup/env.py`
- **Wrong:**
  - `NXTSCAPE_RELEASE_PROVISIONING_PROFILE`
  - `NXTSCAPE_RELEASE_IDENTITY_NAME`
  - `NXTSCAPE_RELEASE_TEAM_ID`
  - `NXTSCAPE_MACOS_KEYCHAIN_PASSWORD`
- **Correct:**
  - `MACOS_CERTIFICATE_NAME`
  - `PROD_MACOS_NOTARIZATION_APPLE_ID`
  - `PROD_MACOS_NOTARIZATION_TEAM_ID`
  - `PROD_MACOS_NOTARIZATION_PWD`
- **Impact:** Signing would fail due to checking wrong environment variables

### 3. ❌ Missing Windows Signing Environment Variables
**File:** `cli/modules/setup/env.py`
- **Missing:** Windows signing environment check entirely
- **Added:**
  - `CODE_SIGN_TOOL_PATH`
  - `ESIGNER_USERNAME`
  - `ESIGNER_PASSWORD`
  - `ESIGNER_TOTP_SECRET`
  - `ESIGNER_CREDENTIAL_ID`
- **Impact:** Windows builds wouldn't validate signing environment properly

## Lessons Learned

1. **Always verify against source**: When wrapping existing code, MUST check exact variable names, paths, and function signatures
2. **Platform differences matter**: Windows and macOS have completely different signing requirements
3. **Consistency is critical**: Using wrong environment variable names breaks compatibility with existing CI/CD

## Current Status

✅ All wrapped modules now use correct:
- Environment variable names matching original code
- Directory paths consistent with BuildContext definitions
- Platform-specific requirements properly handled

## Testing

All 11 modules successfully:
- Load without errors
- Have correct attributes
- Use proper environment variables
- Reference correct paths