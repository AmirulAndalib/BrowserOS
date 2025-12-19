diff --git a/chrome/browser/win/chrome_browser_main_extra_parts_win.cc b/chrome/browser/win/chrome_browser_main_extra_parts_win.cc
new file mode 100644
index 0000000000000..4be0e5418a39c
--- /dev/null
+++ b/chrome/browser/win/chrome_browser_main_extra_parts_win.cc
@@ -0,0 +1,31 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#include "chrome/browser/win/chrome_browser_main_extra_parts_win.h"
+
+#include "base/logging.h"
+#include "chrome/browser/buildflags.h"
+
+#if BUILDFLAG(ENABLE_WINSPARKLE)
+#include "chrome/browser/win/winsparkle_glue.h"
+#endif
+
+ChromeBrowserMainExtraPartsWin::ChromeBrowserMainExtraPartsWin() = default;
+ChromeBrowserMainExtraPartsWin::~ChromeBrowserMainExtraPartsWin() = default;
+
+void ChromeBrowserMainExtraPartsWin::PostBrowserStart() {
+#if BUILDFLAG(ENABLE_WINSPARKLE)
+  // Initialize WinSparkle after the browser UI is ready.
+  // WinSparkle documentation recommends initializing after the main window
+  // is shown, which PostBrowserStart() guarantees.
+  winsparkle_glue::Initialize();
+#endif
+}
+
+void ChromeBrowserMainExtraPartsWin::PostMainMessageLoopRun() {
+#if BUILDFLAG(ENABLE_WINSPARKLE)
+  // Clean up WinSparkle before shutdown.
+  winsparkle_glue::Cleanup();
+#endif
+}
