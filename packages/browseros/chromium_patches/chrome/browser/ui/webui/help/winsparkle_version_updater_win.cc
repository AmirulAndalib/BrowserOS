diff --git a/chrome/browser/ui/webui/help/winsparkle_version_updater_win.cc b/chrome/browser/ui/webui/help/winsparkle_version_updater_win.cc
new file mode 100644
index 0000000000000..09692b4163719
--- /dev/null
+++ b/chrome/browser/ui/webui/help/winsparkle_version_updater_win.cc
@@ -0,0 +1,115 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#include "chrome/browser/ui/webui/help/winsparkle_version_updater_win.h"
+
+#include "base/logging.h"
+#include "base/strings/string_number_conversions.h"
+#include "base/strings/utf_string_conversions.h"
+#include "chrome/browser/win/winsparkle_glue.h"
+
+WinSparkleVersionUpdater::WinSparkleVersionUpdater() {
+  winsparkle_glue::AddObserver(this);
+}
+
+WinSparkleVersionUpdater::~WinSparkleVersionUpdater() {
+  winsparkle_glue::RemoveObserver(this);
+}
+
+void WinSparkleVersionUpdater::CheckForUpdate(StatusCallback status_callback,
+                                               PromoteCallback promote_callback) {
+  status_callback_ = std::move(status_callback);
+
+  if (!winsparkle_glue::IsEnabled()) {
+    LOG(ERROR) << "WinSparkleVersionUpdater: WinSparkle not available";
+    if (!status_callback_.is_null()) {
+      status_callback_.Run(FAILED, 0, false, false, std::string(), 0,
+                           u"WinSparkle updater not available");
+    }
+    return;
+  }
+
+  // Notify that we're starting the check.
+  if (!status_callback_.is_null()) {
+    status_callback_.Run(CHECKING, 0, false, false, std::string(), 0,
+                         std::u16string());
+  }
+
+  // Trigger the update check. WinSparkle will show its built-in UI.
+  winsparkle_glue::CheckForUpdates();
+}
+
+void WinSparkleVersionUpdater::OnWinSparkleStatusChanged(
+    winsparkle_glue::WinSparkleStatus status) {
+  if (status_callback_.is_null()) {
+    return;
+  }
+
+  Status update_status = CHECKING;
+  std::u16string message;
+
+  switch (status) {
+    case winsparkle_glue::WinSparkleStatus::kIdle:
+      // Don't notify for idle state changes.
+      return;
+
+    case winsparkle_glue::WinSparkleStatus::kChecking:
+      update_status = CHECKING;
+      break;
+
+    case winsparkle_glue::WinSparkleStatus::kUpdateAvailable:
+      // Update found, WinSparkle is showing its dialog.
+      // We report as UPDATING since the user is interacting with the update UI.
+      update_status = UPDATING;
+      break;
+
+    case winsparkle_glue::WinSparkleStatus::kDownloading:
+      update_status = UPDATING;
+      break;
+
+    case winsparkle_glue::WinSparkleStatus::kReadyToInstall:
+    case winsparkle_glue::WinSparkleStatus::kInstalling:
+      update_status = NEARLY_UPDATED;
+      break;
+
+    case winsparkle_glue::WinSparkleStatus::kUpToDate:
+      update_status = UPDATED;
+      break;
+
+    case winsparkle_glue::WinSparkleStatus::kError:
+      update_status = FAILED;
+      message = u"Update check failed";
+      break;
+  }
+
+  status_callback_.Run(update_status, 0, false, false, std::string(), 0,
+                       message);
+}
+
+void WinSparkleVersionUpdater::OnWinSparkleProgress(int percent_complete) {
+  if (status_callback_.is_null()) {
+    return;
+  }
+
+  VLOG(2) << "WinSparkleVersionUpdater: Progress " << percent_complete << "%";
+
+  std::u16string message =
+      u"Downloading update: " +
+      base::ASCIIToUTF16(base::NumberToString(percent_complete)) + u"%";
+
+  status_callback_.Run(UPDATING, percent_complete, false, false, std::string(),
+                       0, message);
+}
+
+void WinSparkleVersionUpdater::OnWinSparkleError(
+    const std::string& error_message) {
+  if (status_callback_.is_null()) {
+    return;
+  }
+
+  LOG(ERROR) << "WinSparkleVersionUpdater: Error - " << error_message;
+
+  status_callback_.Run(FAILED, 0, false, false, std::string(), 0,
+                       base::UTF8ToUTF16(error_message));
+}
