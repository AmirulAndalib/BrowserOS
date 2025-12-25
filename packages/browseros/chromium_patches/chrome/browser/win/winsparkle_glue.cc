diff --git a/chrome/browser/win/winsparkle_glue.cc b/chrome/browser/win/winsparkle_glue.cc
new file mode 100644
index 0000000000000..2add8ab388ba4
--- /dev/null
+++ b/chrome/browser/win/winsparkle_glue.cc
@@ -0,0 +1,282 @@
+// Copyright 2024 BrowserOS Authors. All rights reserved.
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#include "chrome/browser/win/winsparkle_glue.h"
+
+#include <string>
+
+#include "base/command_line.h"
+#include "base/functional/bind.h"
+#include "base/logging.h"
+#include "base/no_destructor.h"
+#include "base/observer_list.h"
+#include "base/strings/string_number_conversions.h"
+#include "base/time/time.h"
+#include "base/version.h"
+#include "chrome/browser/browser_process.h"
+#include "chrome/browser/lifetime/application_lifetime_desktop.h"
+#include "chrome/browser/upgrade_detector/build_state.h"
+#include "content/public/browser/browser_task_traits.h"
+#include "content/public/browser/browser_thread.h"
+
+#include <winsparkle.h>
+
+namespace winsparkle_glue {
+
+namespace {
+
+// Appcast URL for Windows x64 updates.
+constexpr char kAppcastUrl[] = "https://cdn.browseros.com/appcast-windows-x64.xml";
+
+// EdDSA public key for signature verification (same as macOS Sparkle).
+constexpr char kEdDSAPublicKey[] = "LzQmcNuTsdB3/dsivo0eeN+jPfDoriRHAkkEJcfFs2A=";
+
+// Update check interval in seconds (1 hour - WinSparkle minimum).
+constexpr int kUpdateCheckIntervalSeconds = 3600;
+
+// Global state.
+bool g_initialized = false;
+WinSparkleStatus g_status = WinSparkleStatus::kIdle;
+bool g_update_ready = false;
+std::string g_pending_version;
+std::string g_last_error;
+
+base::ObserverList<WinSparkleObserver>& GetObservers() {
+  static base::NoDestructor<base::ObserverList<WinSparkleObserver>> observers;
+  return *observers;
+}
+
+// Notify the Chromium upgrade system that an update is ready.
+// This triggers the app menu badge to appear.
+void NotifyUpgradeReady(const std::string& version) {
+  DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
+
+  if (!g_browser_process) {
+    LOG(WARNING) << "WinSparkle: Cannot notify upgrade - no browser process";
+    return;
+  }
+
+  BuildState* build_state = g_browser_process->GetBuildState();
+  if (!build_state) {
+    LOG(WARNING) << "WinSparkle: Cannot notify upgrade - no build state";
+    return;
+  }
+
+  VLOG(1) << "WinSparkle: Notifying upgrade system, version " << version;
+  build_state->SetUpdate(BuildState::UpdateType::kNormalUpdate,
+                         base::Version(version), std::nullopt);
+}
+
+// Set status and notify observers. Must be called on UI thread.
+void SetStatusOnUIThread(WinSparkleStatus status,
+                         const std::string& error_message = std::string()) {
+  DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
+
+  g_status = status;
+  if (!error_message.empty()) {
+    g_last_error = error_message;
+  }
+
+  for (WinSparkleObserver& observer : GetObservers()) {
+    observer.OnWinSparkleStatusChanged(status);
+    if (!error_message.empty()) {
+      observer.OnWinSparkleError(error_message);
+    }
+  }
+}
+
+// Post status change to UI thread.
+void PostStatusChange(WinSparkleStatus status,
+                      const std::string& error_message = std::string()) {
+  content::GetUIThreadTaskRunner({})->PostTask(
+      FROM_HERE,
+      base::BindOnce(&SetStatusOnUIThread, status, error_message));
+}
+
+// Handle update ready notification on UI thread.
+void HandleUpdateReadyOnUIThread(const std::string& version) {
+  DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
+
+  g_update_ready = true;
+  g_pending_version = version;
+  SetStatusOnUIThread(WinSparkleStatus::kReadyToInstall);
+  NotifyUpgradeReady(version);
+}
+
+// WinSparkle Callbacks
+// These are called from WinSparkle's background thread, NOT the UI thread.
+
+int __cdecl CanShutdownCallback() {
+  // This callback asks: "Can the application be closed now?"
+  // We check if all browsers can be closed (no pending downloads, etc.)
+  // Note: This is called from a background thread, but AreAllBrowsersCloseable
+  // should be safe to call as it only checks state.
+  return chrome::AreAllBrowsersCloseable() ? 1 : 0;
+}
+
+void __cdecl ShutdownRequestCallback() {
+  // WinSparkle is asking us to shut down so it can install the update.
+  // Post to UI thread since browser shutdown must happen there.
+  LOG(INFO) << "WinSparkle: Shutdown requested for update installation";
+  content::GetUIThreadTaskRunner({})->PostTask(
+      FROM_HERE,
+      base::BindOnce(&chrome::CloseAllBrowsersAndQuit));
+}
+
+void __cdecl DidFindUpdateCallback() {
+  LOG(INFO) << "WinSparkle: Update found";
+  PostStatusChange(WinSparkleStatus::kUpdateAvailable);
+}
+
+void __cdecl DidNotFindUpdateCallback() {
+  LOG(INFO) << "WinSparkle: No update available (up to date)";
+  PostStatusChange(WinSparkleStatus::kUpToDate);
+}
+
+void __cdecl UpdateCancelledCallback() {
+  LOG(INFO) << "WinSparkle: Update cancelled by user";
+  PostStatusChange(WinSparkleStatus::kIdle);
+}
+
+void __cdecl ErrorCallback() {
+  LOG(ERROR) << "WinSparkle: Update error occurred";
+  PostStatusChange(WinSparkleStatus::kError, "Update check failed");
+}
+
+void __cdecl UpdateDownloadedCallback() {
+  // Update has been downloaded and is ready to install.
+  // WinSparkle doesn't provide the version in this callback,
+  // so we use a placeholder. The important thing is the update is ready.
+  LOG(INFO) << "WinSparkle: Update downloaded and ready to install";
+  content::GetUIThreadTaskRunner({})->PostTask(
+      FROM_HERE,
+      base::BindOnce(&HandleUpdateReadyOnUIThread, "latest"));
+}
+
+}  // namespace
+
+void Initialize() {
+  DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
+
+  if (g_initialized) {
+    VLOG(1) << "WinSparkle: Already initialized";
+    return;
+  }
+
+  LOG(INFO) << "WinSparkle: Initializing...";
+
+  // Check for command-line override of appcast URL (for testing).
+  std::string appcast_url = kAppcastUrl;
+  auto* cmd = base::CommandLine::ForCurrentProcess();
+  if (cmd && cmd->HasSwitch("winsparkle-appcast-url")) {
+    appcast_url = cmd->GetSwitchValueASCII("winsparkle-appcast-url");
+    LOG(WARNING) << "WinSparkle: Using custom appcast URL: " << appcast_url;
+  }
+
+  // 1. Set EdDSA public key for signature verification.
+  win_sparkle_set_eddsa_public_key(kEdDSAPublicKey);
+
+  // 2. Set appcast URL.
+  win_sparkle_set_appcast_url(appcast_url.c_str());
+
+  // 3. Enable automatic background update checks.
+  win_sparkle_set_automatic_check_for_updates(1);
+  win_sparkle_set_update_check_interval(kUpdateCheckIntervalSeconds);
+
+  // 4. Set shutdown callbacks - these are required for update installation.
+  win_sparkle_set_can_shutdown_callback(CanShutdownCallback);
+  win_sparkle_set_shutdown_request_callback(ShutdownRequestCallback);
+
+  // 5. Set update status callbacks.
+  win_sparkle_set_did_find_update_callback(DidFindUpdateCallback);
+  win_sparkle_set_did_not_find_update_callback(DidNotFindUpdateCallback);
+  win_sparkle_set_update_cancelled_callback(UpdateCancelledCallback);
+  win_sparkle_set_error_callback(ErrorCallback);
+
+  // 6. Initialize WinSparkle - this starts the automatic checking.
+  win_sparkle_init();
+
+  g_initialized = true;
+  g_status = WinSparkleStatus::kIdle;
+
+  LOG(INFO) << "WinSparkle: Initialized successfully";
+  LOG(INFO) << "WinSparkle: Appcast URL: " << appcast_url;
+  LOG(INFO) << "WinSparkle: Update check interval: "
+            << kUpdateCheckIntervalSeconds << " seconds";
+
+  // Check for force-check flag (for testing).
+  if (cmd && cmd->HasSwitch("winsparkle-force-check")) {
+    LOG(INFO) << "WinSparkle: Force check requested via command line";
+    // Delay the check slightly to ensure UI is fully ready.
+    content::GetUIThreadTaskRunner({})->PostDelayedTask(
+        FROM_HERE,
+        base::BindOnce(&CheckForUpdates),
+        base::Seconds(2));
+  }
+}
+
+void Cleanup() {
+  DCHECK_CURRENTLY_ON(content::BrowserThread::UI);
+
+  if (!g_initialized) {
+    return;
+  }
+
+  LOG(INFO) << "WinSparkle: Cleaning up...";
+  win_sparkle_cleanup();
+  g_initialized = false;
+  g_status = WinSparkleStatus::kIdle;
+  g_update_ready = false;
+  g_pending_version.clear();
+  g_last_error.clear();
+  LOG(INFO) << "WinSparkle: Cleanup complete";
+}
+
+bool IsEnabled() {
+  return g_initialized;
+}
+
+void CheckForUpdates() {
+  if (!g_initialized) {
+    LOG(WARNING) << "WinSparkle: Cannot check for updates - not initialized";
+    return;
+  }
+
+  LOG(INFO) << "WinSparkle: Checking for updates (user-initiated)";
+  g_status = WinSparkleStatus::kChecking;
+
+  for (WinSparkleObserver& observer : GetObservers()) {
+    observer.OnWinSparkleStatusChanged(WinSparkleStatus::kChecking);
+  }
+
+  // Post the WinSparkle call as a separate task to avoid blocking-disallowed
+  // scope issues. WinSparkle's win_sparkle_check_update_with_ui() may do
+  // blocking operations (window creation, etc.) that trigger DCHECK failures
+  // when called from within Mojo/WebUI handler contexts.
+  content::GetUIThreadTaskRunner({})->PostTask(
+      FROM_HERE,
+      base::BindOnce([]() {
+        if (g_initialized) {
+          win_sparkle_check_update_with_ui();
+        }
+      }));
+}
+
+bool IsUpdateReady() {
+  return g_update_ready;
+}
+
+WinSparkleStatus GetStatus() {
+  return g_status;
+}
+
+void AddObserver(WinSparkleObserver* observer) {
+  GetObservers().AddObserver(observer);
+}
+
+void RemoveObserver(WinSparkleObserver* observer) {
+  GetObservers().RemoveObserver(observer);
+}
+
+}  // namespace winsparkle_glue
