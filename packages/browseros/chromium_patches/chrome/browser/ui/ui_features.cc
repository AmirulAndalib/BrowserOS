diff --git a/chrome/browser/ui/ui_features.cc b/chrome/browser/ui/ui_features.cc
index c03c8ac6f6e00..04edb9e546aec 100644
--- a/chrome/browser/ui/ui_features.cc
+++ b/chrome/browser/ui/ui_features.cc
@@ -260,6 +260,14 @@ bool IsSideBySideKeyboardShortcutEnabled() {
 
 BASE_FEATURE(kSidePanelResizing, base::FEATURE_ENABLED_BY_DEFAULT);
 
+BASE_FEATURE(kThirdPartyLlmPanel,
+             "ThirdPartyLlmPanel",
+             base::FEATURE_ENABLED_BY_DEFAULT);
+
+BASE_FEATURE(kClashOfGpts,
+             "ClashOfGpts",
+             base::FEATURE_ENABLED_BY_DEFAULT);
+
 BASE_FEATURE(kTabDuplicateMetrics, base::FEATURE_ENABLED_BY_DEFAULT);
 
 // Enables buttons when scrolling the tabstrip https://crbug.com/951078
