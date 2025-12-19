diff --git a/chrome/browser/win/chrome_browser_main_extra_parts_win.h b/chrome/browser/win/chrome_browser_main_extra_parts_win.h
new file mode 100644
index 0000000000000..40ee667761c46
--- /dev/null
+++ b/chrome/browser/win/chrome_browser_main_extra_parts_win.h
@@ -0,0 +1,24 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#ifndef CHROME_BROWSER_WIN_CHROME_BROWSER_MAIN_EXTRA_PARTS_WIN_H_
+#define CHROME_BROWSER_WIN_CHROME_BROWSER_MAIN_EXTRA_PARTS_WIN_H_
+
+#include "chrome/browser/chrome_browser_main_extra_parts.h"
+
+// Windows-specific browser initialization.
+// Currently used for WinSparkle auto-updater integration.
+class ChromeBrowserMainExtraPartsWin : public ChromeBrowserMainExtraParts {
+ public:
+  ChromeBrowserMainExtraPartsWin();
+  ChromeBrowserMainExtraPartsWin(const ChromeBrowserMainExtraPartsWin&) = delete;
+  ChromeBrowserMainExtraPartsWin& operator=(const ChromeBrowserMainExtraPartsWin&) = delete;
+  ~ChromeBrowserMainExtraPartsWin() override;
+
+  // ChromeBrowserMainExtraParts:
+  void PostBrowserStart() override;
+  void PostMainMessageLoopRun() override;
+};
+
+#endif  // CHROME_BROWSER_WIN_CHROME_BROWSER_MAIN_EXTRA_PARTS_WIN_H_
