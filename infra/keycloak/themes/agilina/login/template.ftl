<#-- The frame of every Keycloak page in the Agilina look. It keeps the contract of the base
     template (`registrationLayout` and its sections) so that any page of Keycloak fits in it;
     only the markup and the classes are ours. The classes are Tailwind utilities, compiled
     from the same tokens as the web. -->
<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false>
<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}"<#if realm.internationalizationEnabled> lang="${locale.currentLanguageTag}" dir="${(locale.rtl)?then('rtl','ltr')}"</#if>>

<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="robots" content="noindex, nofollow">
    <title>${msg("loginTitle",(realm.displayName!''))}</title>
    <link rel="icon" href="${url.resourcesPath}/img/favicon.svg" type="image/svg+xml" />
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <script type="importmap">
        {
            "imports": {
                "rfc4648": "${url.resourcesCommonPath}/vendor/rfc4648/rfc4648.js"
            }
        }
    </script>
    <script type="module">
        import { startSessionPolling } from "${url.resourcesPath}/js/authChecker.js";

        startSessionPolling(
          "${url.ssoLoginInOtherTabsUrl?no_esc}"
        );
    </script>
</head>

<body class="min-h-dvh bg-[radial-gradient(60rem_32rem_at_50%_-8rem,color-mix(in_oklab,var(--color-accent)_16%,transparent),transparent)]">
<div class="mx-auto flex min-h-dvh w-full max-w-md flex-col px-4 pb-10">

    <header class="flex justify-end pt-4">
        <#if realm.internationalizationEnabled && locale.supported?size gt 1>
            <nav id="kc-locale" aria-label="${msg("languages")}" class="flex items-center gap-1 text-sm text-muted">
                <!-- Lucide "languages" icon. -->
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-4" aria-hidden="true">
                    <path d="m5 8 6 6" /><path d="m4 14 6-6 2-3" /><path d="M2 5h12" /><path d="M7 2h1" /><path d="m22 22-5-10-5 10" /><path d="M14 18h6" />
                </svg>
                <#list locale.supported as l>
                    <#if l.languageTag == locale.currentLanguageTag>
                        <span aria-current="true" class="rounded-md px-2 py-1 font-semibold text-foreground">${l.languageTag?upper_case}</span>
                    <#else>
                        <a href="${l.url}" lang="${l.languageTag}" class="rounded-md px-2 py-1 hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent">${l.languageTag?upper_case}</a>
                    </#if>
                </#list>
            </nav>
        </#if>
    </header>

    <div class="mt-10 flex flex-col items-center text-center">
        <span class="flex size-12 items-center justify-center rounded-2xl bg-accent text-accent-foreground shadow-sm">
            <!-- Lucide "bot" icon. -->
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="size-6" aria-hidden="true">
                <path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />
            </svg>
        </span>
        <div id="kc-header-wrapper" class="mt-4 font-display text-3xl font-bold tracking-tight">${kcSanitize(msg("loginTitleHtml",(realm.displayNameHtml!'')))?no_esc}</div>
        <p class="mt-1 text-sm text-muted">${msg("agilinaTagline")}</p>
    </div>

    <main class="mt-8 rounded-2xl border border-border bg-surface p-6 shadow-sm sm:p-8">
        <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
            <h1 id="kc-page-title" class="font-display text-xl font-semibold"><#nested "header"></h1>
        <#else>
            <#nested "show-username">
            <div id="kc-username" class="mt-1 flex items-center gap-2 text-sm">
                <span id="kc-attempted-username" class="font-medium">${auth.attemptedUsername}</span>
                <a id="reset-login" href="${url.loginRestartFlowUrl}" class="text-accent underline-offset-2 hover:underline">${msg("restartLoginTooltip")}</a>
            </div>
        </#if>

        <div id="kc-content" class="mt-4">
            <#-- A message of the flow (a refused login, an expired session). Never warns about the
                 action itself when an application asked for it (same rule as the base theme). -->
            <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
                <div role="<#if message.type = 'error'>alert<#else>status</#if>"
                     class="mb-4 rounded-lg border px-3 py-2 text-sm <#if message.type = 'error'>border-danger/30 bg-danger/5 text-danger<#else>border-border bg-background text-foreground</#if>">
                    ${kcSanitize(message.summary)?no_esc}
                </div>
            </#if>

            <#nested "form">

            <#if auth?has_content && auth.showTryAnotherWayLink()>
                <form id="kc-select-try-another-way-form" action="${url.loginAction}" method="post" class="mt-4">
                    <input type="hidden" name="tryAnotherWay" value="on"/>
                    <a href="#" id="try-another-way" class="text-sm text-accent underline-offset-2 hover:underline"
                       onclick="document.forms['kc-select-try-another-way-form'].requestSubmit();return false;">${msg("doTryAnotherWay")}</a>
                </form>
            </#if>

            <#nested "socialProviders">
        </div>
    </main>

    <#if displayInfo>
        <div id="kc-info" class="mt-6 text-center text-sm text-muted"><#nested "info"></div>
    </#if>
</div>
</body>
</html>
</#macro>
