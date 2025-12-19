diff --git a/chrome/browser/win/winsparkle_glue.h b/chrome/browser/win/winsparkle_glue.h
new file mode 100644
index 0000000000000..eabf4885619f5
--- /dev/null
+++ b/chrome/browser/win/winsparkle_glue.h
@@ -0,0 +1,60 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#ifndef CHROME_BROWSER_WIN_WINSPARKLE_GLUE_H_
+#define CHROME_BROWSER_WIN_WINSPARKLE_GLUE_H_
+
+#include <string>
+
+#include "base/observer_list_types.h"
+
+namespace winsparkle_glue {
+
+// WinSparkle updater status codes.
+enum class WinSparkleStatus {
+  kIdle = 0,
+  kChecking,
+  kUpdateAvailable,
+  kDownloading,
+  kReadyToInstall,
+  kInstalling,
+  kUpToDate,
+  kError,
+};
+
+// Observer interface for WinSparkle update status changes.
+// Callbacks are always invoked on the UI thread.
+class WinSparkleObserver : public base::CheckedObserver {
+ public:
+  virtual void OnWinSparkleStatusChanged(WinSparkleStatus status) {}
+  virtual void OnWinSparkleProgress(int percent_complete) {}
+  virtual void OnWinSparkleError(const std::string& error_message) {}
+};
+
+// Initialize WinSparkle. Must be called after the main window is shown.
+// Safe to call multiple times; subsequent calls are no-ops.
+void Initialize();
+
+// Cleanup WinSparkle. Called during browser shutdown.
+void Cleanup();
+
+// Returns true if WinSparkle is initialized and available.
+bool IsEnabled();
+
+// Check for updates with UI. Shows WinSparkle's built-in update dialog.
+void CheckForUpdates();
+
+// Returns true if an update has been downloaded and is ready to install.
+bool IsUpdateReady();
+
+// Returns the current status.
+WinSparkleStatus GetStatus();
+
+// Observer management.
+void AddObserver(WinSparkleObserver* observer);
+void RemoveObserver(WinSparkleObserver* observer);
+
+}  // namespace winsparkle_glue
+
+#endif  // CHROME_BROWSER_WIN_WINSPARKLE_GLUE_H_
