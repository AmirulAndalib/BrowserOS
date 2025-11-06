diff --git a/chrome/browser/prefs/browser_prefs.cc b/chrome/browser/prefs/browser_prefs.cc
index 12845dd2464bb..322e32e50f44a 100644
--- a/chrome/browser/prefs/browser_prefs.cc
+++ b/chrome/browser/prefs/browser_prefs.cc
@@ -24,6 +24,7 @@
 #include "chrome/browser/accessibility/prefers_default_scrollbar_styles_prefs.h"
 #include "chrome/browser/actor/ui/actor_ui_state_manager_prefs.h"
 #include "chrome/browser/browser_process_impl.h"
+#include "chrome/browser/browseros_server/browseros_server_prefs.h"
 #include "chrome/browser/chrome_content_browser_client.h"
 #include "chrome/browser/component_updater/component_updater_prefs.h"
 #include "chrome/browser/download/download_prefs.h"
@@ -106,6 +107,7 @@
 #include "components/breadcrumbs/core/breadcrumbs_status.h"
 #include "components/browsing_data/core/pref_names.h"
 #include "components/certificate_transparency/pref_names.h"
+#include "components/metrics/browseros_metrics/browseros_metrics_prefs.h"
 #include "components/collaboration/public/pref_names.h"
 #include "components/commerce/core/pref_names.h"
 #include "components/content_settings/core/browser/host_content_settings_map.h"
@@ -1738,6 +1740,8 @@ void RegisterLocalState(PrefRegistrySimple* registry) {
   breadcrumbs::RegisterPrefs(registry);
   browser_shutdown::RegisterPrefs(registry);
   BrowserProcessImpl::RegisterPrefs(registry);
+  browseros_server::RegisterLocalStatePrefs(registry);
+  browseros_metrics::RegisterLocalStatePrefs(registry);
   ChromeContentBrowserClient::RegisterLocalStatePrefs(registry);
   chrome_labs_prefs::RegisterLocalStatePrefs(registry);
   chrome_urls::RegisterPrefs(registry);
@@ -2038,6 +2042,7 @@ void RegisterProfilePrefs(user_prefs::PrefRegistrySyncable* registry,
   AnnouncementNotificationService::RegisterProfilePrefs(registry);
   autofill::prefs::RegisterProfilePrefs(registry);
   browsing_data::prefs::RegisterBrowserUserPrefs(registry);
+  browseros_metrics::RegisterProfilePrefs(registry);
   capture_policy::RegisterProfilePrefs(registry);
   certificate_transparency::prefs::RegisterPrefs(registry);
   ChromeContentBrowserClient::RegisterProfilePrefs(registry);
@@ -2109,6 +2114,7 @@ void RegisterProfilePrefs(user_prefs::PrefRegistrySyncable* registry,
   regional_capabilities::prefs::RegisterProfilePrefs(registry);
   RegisterBrowserUserPrefs(registry);
   RegisterGeminiSettingsPrefs(registry);
+  RegisterNxtscapePrefs(registry);
   RegisterPrefersDefaultScrollbarStylesPrefs(registry);
   RegisterSafetyHubProfilePrefs(registry);
 #if BUILDFLAG(IS_CHROMEOS)
@@ -2508,6 +2514,46 @@ void RegisterGeminiSettingsPrefs(user_prefs::PrefRegistrySyncable* registry) {
   registry->RegisterIntegerPref(prefs::kGeminiSettings, 0);
 }
 
+void RegisterNxtscapePrefs(user_prefs::PrefRegistrySyncable* registry) {
+  // AI Provider configurations stored as JSON
+  // This will store the entire provider configuration including:
+  // - defaultProviderId
+  // - providers array with all configured providers
+  registry->RegisterStringPref(prefs::kBrowserOSProviders, "");
+  
+  // Legacy preferences (kept for backward compatibility)
+  registry->RegisterStringPref("nxtscape.default_provider", "browseros");
+  
+  // Nxtscape provider settings
+  registry->RegisterStringPref("nxtscape.nxtscape_model", "");
+
+  // OpenAI provider settings
+  registry->RegisterStringPref("nxtscape.openai_api_key", "");
+  registry->RegisterStringPref("nxtscape.openai_model", "gpt-4o");
+  registry->RegisterStringPref("nxtscape.openai_base_url", "");
+
+  // Anthropic provider settings
+  registry->RegisterStringPref("nxtscape.anthropic_api_key", "");
+  registry->RegisterStringPref("nxtscape.anthropic_model", "claude-3-5-sonnet-latest");
+  registry->RegisterStringPref("nxtscape.anthropic_base_url", "");
+
+  // Gemini provider settings
+  registry->RegisterStringPref("nxtscape.gemini_api_key", "");
+  registry->RegisterStringPref("nxtscape.gemini_model", "gemini-1.5-pro");
+  registry->RegisterStringPref("nxtscape.gemini_base_url", "");
+
+  // Ollama provider settings
+  registry->RegisterStringPref("nxtscape.ollama_api_key", "");
+  registry->RegisterStringPref("nxtscape.ollama_base_url", "http://localhost:11434");
+  registry->RegisterStringPref("nxtscape.ollama_model", "");
+  
+  // BrowserOS toolbar settings
+  registry->RegisterBooleanPref(prefs::kBrowserOSShowToolbarLabels, true);
+  
+  // Custom providers list - stored as a JSON string
+  registry->RegisterStringPref(prefs::kBrowserOSCustomProviders, "[]");
+}
+
 #if BUILDFLAG(IS_CHROMEOS)
 void RegisterSigninProfilePrefs(user_prefs::PrefRegistrySyncable* registry,
                                 std::string_view country) {
