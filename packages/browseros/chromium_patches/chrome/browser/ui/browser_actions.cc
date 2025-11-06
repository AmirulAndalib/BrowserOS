diff --git a/chrome/browser/ui/browser_actions.cc b/chrome/browser/ui/browser_actions.cc
index fb3dba200be8c..87ca8bd207bb1 100644
--- a/chrome/browser/ui/browser_actions.cc
+++ b/chrome/browser/ui/browser_actions.cc
@@ -206,6 +206,10 @@ void BrowserActions::InitializeBrowserActions() {
   Profile* const profile = base::to_address(profile_);
   TabStripModel* const tab_strip_model = bwi_->GetTabStripModel();
   BrowserWindowInterface* const bwi = base::to_address(bwi_);
+  Browser* const browser =
+      BrowserView::GetBrowserViewForBrowser(bwi)
+          ? BrowserView::GetBrowserViewForBrowser(bwi)->browser()
+          : nullptr;
   const bool is_guest_session = profile_->IsGuestSession();
 
   actions::ActionManager::Get().AddAction(
@@ -253,6 +257,34 @@ void BrowserActions::InitializeBrowserActions() {
             .Build());
   }
 
+  // Add third-party LLM panel if feature is enabled
+  if (base::FeatureList::IsEnabled(features::kThirdPartyLlmPanel) && browser) {
+    root_action_item_->AddChild(
+        SidePanelAction(SidePanelEntryId::kThirdPartyLlm,
+                        IDS_THIRD_PARTY_LLM_TITLE,
+                        IDS_THIRD_PARTY_LLM_TITLE,
+                        vector_icons::kChatOrangeIcon,
+                        kActionSidePanelShowThirdPartyLlm, bwi, true)
+            .Build());
+  }
+
+  // Add Clash of GPTs action if feature is enabled
+  if (base::FeatureList::IsEnabled(features::kClashOfGpts) && browser) {
+    root_action_item_->AddChild(
+        ChromeMenuAction(
+            base::BindRepeating(
+                [](Browser* browser, actions::ActionItem* item,
+                   actions::ActionInvocationContext context) {
+                  chrome::ExecuteCommand(browser, IDC_OPEN_CLASH_OF_GPTS);
+                },
+                base::Unretained(browser)),
+            kActionSidePanelShowClashOfGpts,
+            IDS_CLASH_OF_GPTS_TITLE,
+            IDS_CLASH_OF_GPTS_TOOLTIP,
+            vector_icons::kClashOfGptsIcon)
+            .Build());
+  }
+
   if (HistorySidePanelCoordinator::IsSupported()) {
     root_action_item_->AddChild(
         SidePanelAction(SidePanelEntryId::kHistory, IDS_HISTORY_TITLE,
