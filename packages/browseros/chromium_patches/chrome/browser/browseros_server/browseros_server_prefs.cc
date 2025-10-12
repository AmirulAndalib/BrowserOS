diff --git a/chrome/browser/browseros_server/browseros_server_prefs.cc b/chrome/browser/browseros_server/browseros_server_prefs.cc
new file mode 100644
index 0000000000000..4065d6d724f63
--- /dev/null
+++ b/chrome/browser/browseros_server/browseros_server_prefs.cc
@@ -0,0 +1,31 @@
+// Copyright 2024 The Chromium Authors
+// Use of this source code is governed by a BSD-style license that can be
+// found in the LICENSE file.
+
+#include "chrome/browser/browseros_server/browseros_server_prefs.h"
+
+#include "components/prefs/pref_registry_simple.h"
+
+namespace browseros_server {
+
+// CDP server port (0 = auto-assign random port on startup)
+const char kCDPServerPort[] = "browseros.server.cdp_port";
+
+// MCP server port (HTTP)
+const char kMCPServerPort[] = "browseros.server.mcp_port";
+
+// Whether MCP server is enabled
+const char kMCPServerEnabled[] = "browseros.server.mcp_enabled";
+
+void RegisterLocalStatePrefs(PrefRegistrySimple* registry) {
+  // CDP port: default 9223
+  registry->RegisterIntegerPref(kCDPServerPort, 9223);
+
+  // MCP port: default 9224
+  registry->RegisterIntegerPref(kMCPServerPort, 9224);
+
+  // MCP enabled
+  registry->RegisterBooleanPref(kMCPServerEnabled, true);
+}
+
+}  // namespace browseros_server
