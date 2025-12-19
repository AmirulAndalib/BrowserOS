diff --git a/chrome/browser/ui/webui/help/version_updater_winsparkle.cc b/chrome/browser/ui/webui/help/version_updater_winsparkle.cc
new file mode 100644
index 0000000000000..28089ab88c422
--- /dev/null
+++ b/chrome/browser/ui/webui/help/version_updater_winsparkle.cc
@@ -0,0 +1,55 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#include "chrome/browser/ui/webui/help/version_updater.h"
+
+#include <memory>
+#include <string>
+
+#include "base/logging.h"
+#include "chrome/browser/buildflags.h"
+#include "chrome/browser/upgrade_detector/upgrade_detector.h"
+
+#if BUILDFLAG(ENABLE_WINSPARKLE)
+#include "chrome/browser/ui/webui/help/winsparkle_version_updater_win.h"
+#include "chrome/browser/win/winsparkle_glue.h"
+#endif
+
+namespace {
+
+// Fallback implementation when WinSparkle is not available.
+// Just checks if a new version is ready (from UpgradeDetector).
+class VersionUpdaterBasic : public VersionUpdater {
+ public:
+  VersionUpdaterBasic() = default;
+  VersionUpdaterBasic(const VersionUpdaterBasic&) = delete;
+  VersionUpdaterBasic& operator=(const VersionUpdaterBasic&) = delete;
+  ~VersionUpdaterBasic() override = default;
+
+  // VersionUpdater implementation.
+  void CheckForUpdate(StatusCallback callback, PromoteCallback) override {
+    const Status status = UpgradeDetector::GetInstance()->is_upgrade_available()
+                              ? NEARLY_UPDATED
+                              : DISABLED;
+    callback.Run(status, 0, false, false, std::string(), 0, std::u16string());
+  }
+};
+
+}  // namespace
+
+std::unique_ptr<VersionUpdater> VersionUpdater::Create(
+    content::WebContents* web_contents) {
+#if BUILDFLAG(ENABLE_WINSPARKLE)
+  // Use WinSparkle updater if it's enabled and initialized.
+  if (winsparkle_glue::IsEnabled()) {
+    LOG(INFO) << "VersionUpdater: Using WinSparkle updater";
+    return std::make_unique<WinSparkleVersionUpdater>();
+  } else {
+    LOG(INFO) << "VersionUpdater: WinSparkle not available, using basic updater";
+  }
+#endif
+
+  // Fall back to basic updater.
+  return std::make_unique<VersionUpdaterBasic>();
+}
