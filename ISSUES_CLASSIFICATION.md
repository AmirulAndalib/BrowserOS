# BrowserOS GitHub Issues Classification

> Generated: 2025-12-02 | Total Open Issues: ~42

## Summary by Category

| Category | Count | Priority |
|----------|-------|----------|
| 🐛 Bugs - Critical | 4 | High |
| 🐛 Bugs - Non-Critical | 5 | Medium |
| 🤖 Feature: AI Model Support | 4 | Medium |
| 🎨 Feature: UI/UX | 5 | Medium |
| 🔧 Feature: Core Functionality | 4 | Low-Medium |
| 📦 Installation/Setup | 2 | High |

---

## 🐛 Bugs - Critical (Need Immediate Attention)

### #208 - Anthropic Sonnet 4.5 always fail in agent mode
- **Author:** mklikushin (Nov 26, 2025)
- **Problem:** Configuration conflict - `top_p` and `temperature` both set causes failure
- **Impact:** High - breaks a major AI provider integration
- **Suggested Action:** Fix parameter handling logic for Anthropic API calls
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #202 - MCP server crashes with SIGILL on Ivy Bridge CPUs
- **Author:** mmmikko (Nov 14, 2025)
- **Problem:** Server crashes on older processors lacking AVX2 support
- **Impact:** High - completely blocks users with older hardware
- **Suggested Action:** Build without AVX2 requirement or provide fallback binary
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #188 - Agent executes webpage instructions
- **Author:** 1Jesper1 (Nov 5, 2025)
- **Problem:** Agent inappropriately follows instructions embedded in websites (prompt injection)
- **Impact:** Critical - Security vulnerability
- **Suggested Action:** Implement input sanitization and instruction boundary detection
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #146 - Anthropic Model Selection Problems
- **Author:** eleqtrizit (Oct 20, 2025)
- **Problem:** Users can't properly select/configure Anthropic models
- **Impact:** High - affects major AI provider
- **Suggested Action:** Debug model selection dropdown and config persistence
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

## 🐛 Bugs - Non-Critical

### #196 - Failed to save provider. Connection lost
- **Author:** Shantaram74 (Nov 11, 2025)
- **Problem:** Provider configuration fails with connection error
- **Impact:** Medium - frustrating UX but likely has workarounds
- **Suggested Action:** Add retry logic and better error messaging
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #187 - Issue with browser window scale size
- **Author:** Shastryji (Nov 5, 2025)
- **Problem:** Window scaling not functioning correctly
- **Impact:** Medium - UI annoyance
- **Suggested Action:** Check DPI/scaling detection logic
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #136 - Some AIs Have Issues with Agent
- **Author:** mymel2001-holder (Oct 12, 2025)
- **Problem:** Certain AI models have compatibility problems with agent
- **Impact:** Medium - depends on which models
- **Suggested Action:** Need more details on which models fail
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #112 - Form Handling Issue
- **Author:** dataneim (Sep 17, 2025)
- **Problem:** Issues with form interaction and handling
- **Impact:** Medium - affects automation capability
- **Suggested Action:** Debug form field detection and input
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #91 - Account Logout Issues
- **Author:** adityasingla71 (Aug 27, 2025)
- **Problem:** Users can't logout properly
- **Impact:** Low-Medium - workaround exists (clear data)
- **Suggested Action:** Fix session/auth token clearing
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

## 📦 Installation/Setup Issues

### #194 - Immediately after install: Error: WebSocket connection
- **Author:** chrisamow (Nov 9, 2025)
- **Problem:** WebSocket connectivity issue post-installation
- **Impact:** High - blocks new users from getting started
- **Suggested Action:** Check firewall, port, and local server startup sequence
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

### #193 - False positive 'Virus Detected' warning from Chrome
- **Author:** dansasser (Nov 8, 2025)
- **Labels:** bug, Feature
- **Problem:** Windows installer triggers false security warnings
- **Impact:** High - scares away new users
- **Suggested Action:** Code sign the installer, submit to Microsoft for analysis
- **Your Reply:** `[ ]` Respond | `[ ]` Investigate | `[ ]` Close

---

## 🤖 Feature Requests: AI Model Support

### #209 - [Feature Request] Add Gemini 3.0 on AI support
- **Author:** Karuto2k7 (Nov 30, 2025)
- **Request:** Integrate Google's latest Gemini model
- **Complexity:** Medium - requires API integration
- **Suggested Action:** Add to AI provider roadmap
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #205 - [Feature Request] Kimi K2
- **Author:** ekonomi-droid (Nov 19, 2025)
- **Request:** Add support for Kimi K2 AI model
- **Complexity:** Medium - new provider integration
- **Suggested Action:** Evaluate API availability and demand
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #148 - Support for Gemini 2.5 Computer Use Model
- **Author:** horni-co (Oct 22, 2025)
- **Request:** Add Gemini with computer use capabilities
- **Complexity:** Medium-High - may require special handling
- **Suggested Action:** Consider bundling with #209
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #98 - Model Recommendations
- **Author:** WhiteTorn (Sep 3, 2025)
- **Request:** Recommend optimal AI models for the platform
- **Complexity:** Low - documentation task
- **Suggested Action:** Create docs page with model recommendations
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

## 🎨 Feature Requests: UI/UX

### #207 - [Feature Request] Vertical Tabs and Page Translate
- **Author:** Rifat1 (Nov 23, 2025)
- **Request:** Vertical tab organization + webpage translation
- **Complexity:** High - significant UI changes
- **Suggested Action:** Split into two separate issues
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #200 - [Feature Request] Organize tabs
- **Author:** theUpsider (Nov 13, 2025)
- **Request:** Improved tab management capabilities
- **Complexity:** Medium
- **Suggested Action:** Define specific features (groups, save sessions, etc.)
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #185 - [Feature Request] Help me Write in right click context menu
- **Author:** jspurrier (Nov 4, 2025)
- **Labels:** enhancement, Feature
- **Request:** AI writing assistance via context menu
- **Complexity:** Medium - context menu + AI integration
- **Suggested Action:** Good feature for improving daily usage
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #100 - Input Bar Scrolling Problem
- **Author:** thekrishnajeena (Sep 7, 2025)
- **Labels:** Bug, Good First Issue
- **Request:** Input bar should stay fixed, not scroll with content
- **Complexity:** Low - CSS/layout fix
- **Suggested Action:** Good first issue for new contributors
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #94 - Dark Mode Theme Inconsistency
- **Author:** anujchoudhary-17 (Sep 1, 2025)
- **Labels:** Enhancement, Good First Issue
- **Request:** Dropdown menus should match dark mode styling
- **Complexity:** Low - CSS fix
- **Suggested Action:** Good first issue for new contributors
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

## 🔧 Feature Requests: Core Functionality

### #145 - Custom MCP Integration
- **Author:** xjk2000 (Oct 20, 2025)
- **Request:** Enable integration with custom MCP servers
- **Complexity:** Medium - extends existing MCP support
- **Suggested Action:** Valuable for power users
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #131 - Remove Google Dependencies
- **Author:** DefenderOfChrist (Oct 2, 2025)
- **Request:** Eliminate reliance on Google services
- **Complexity:** High - significant refactoring
- **Suggested Action:** Evaluate which dependencies and their alternatives
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #129 - Automatic Updating Feature
- **Author:** qlam699 (Oct 2, 2025)
- **Request:** Auto-update software
- **Complexity:** Medium-High - requires update server infrastructure
- **Suggested Action:** Important for user retention
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

### #114 - Voice Command Sidebar
- **Author:** neptotech (Sep 18, 2025)
- **Request:** Voice command functionality in agent sidebar
- **Complexity:** Medium - needs speech recognition integration
- **Suggested Action:** Cool feature, evaluate priority
- **Your Reply:** `[ ]` Accept | `[ ]` Decline | `[ ]` Need More Info

---

## 📋 Action Items Summary

### Immediate Priority (This Week)
1. **#188** - Security issue with prompt injection - CRITICAL
2. **#208** - Anthropic API broken - affects many users
3. **#194** - WebSocket issue blocking new users
4. **#193** - False positive virus warning scaring users

### Short-term (Next 2 Sprints)
1. **#202** - AVX2/older CPU support
2. **#146** - Anthropic model selection
3. **#196** - Provider save connection issues

### Good First Issues (For New Contributors)
1. **#100** - Input bar scrolling (CSS fix)
2. **#94** - Dark mode dropdowns (CSS fix)

### Feature Backlog (Prioritize Based on Demand)
1. **#209** + **#148** - Gemini model support
2. **#185** - Context menu AI writing
3. **#145** - Custom MCP integration
4. **#129** - Auto-updates

---

## Template Responses

### For Bug Reports
```
Thanks for reporting this issue! We're looking into it.

Could you please provide:
1. BrowserOS version
2. Operating system
3. Steps to reproduce
4. Any error messages in the console (View > Developer > Developer Tools)
```

### For Feature Requests (Accepting)
```
Thanks for the suggestion! This aligns with our roadmap and we'd love to add this.

We'll add it to our backlog. PRs are welcome if you'd like to contribute!
```

### For Feature Requests (Needs Discussion)
```
Thanks for the suggestion! Before we proceed, could you help us understand:
1. What's your specific use case?
2. How would you expect this to work?

This will help us design the feature properly.
```

### For Duplicates
```
Thanks for reporting! This appears to be a duplicate of #XXX.

We're tracking progress there. Closing this to keep discussion in one place.
```
