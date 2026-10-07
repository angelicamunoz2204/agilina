<#-- The sign-in page, as in the mockup: email, password, a full-width button and, outside the
     card, the reminder that there is no public registration. -->
<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password') displayInfo=true; section>
    <#if section = "header">
        ${msg("loginAccountTitle")}
    <#elseif section = "form">
        <#if realm.password>
            <form id="kc-form-login" action="${url.loginAction}" method="post" class="flex flex-col"
                  onsubmit="login.disabled = true; return true;">
                <p class="text-sm text-muted">${msg("agilinaLoginSubtitle")}</p>

                <#if !usernameHidden??>
                    <label for="username" class="mt-6 mb-1 text-sm font-medium">${msg("usernameOrEmail")}</label>
                    <input id="username" name="username" value="${(login.username!'')}" type="text"
                           autofocus autocomplete="username" dir="ltr"
                           aria-invalid="<#if messagesPerField.existsError('username','password')>true<#else>false</#if>"
                           <#if messagesPerField.existsError('username','password')>aria-describedby="input-error"</#if>
                           class="block min-h-11 w-full rounded-md border border-border bg-background px-3 py-2 shadow-xs focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent" />
                </#if>

                <label for="password" class="mt-4 mb-1 text-sm font-medium">${msg("password")}</label>
                <input id="password" name="password" type="password" autocomplete="current-password" dir="ltr"
                       aria-invalid="<#if messagesPerField.existsError('username','password')>true<#else>false</#if>"
                       class="block min-h-11 w-full rounded-md border border-border bg-background px-3 py-2 shadow-xs focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-accent" />

                <#-- A refused login. Keycloak says it once for both fields, and with the same text
                     whether the email exists or not (see messages_*.properties). -->
                <#if messagesPerField.existsError('username','password')>
                    <p id="input-error" role="alert" aria-live="polite"
                       class="mt-4 rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
                        ${kcSanitize(messagesPerField.getFirstError('username','password'))?no_esc}
                    </p>
                </#if>

                <#if realm.resetPasswordAllowed>
                    <a href="${url.loginResetCredentialsUrl}" class="mt-3 self-end text-sm text-muted underline-offset-2 hover:text-foreground hover:underline">${msg("doForgotPassword")}</a>
                </#if>

                <input type="hidden" id="id-hidden-input" name="credentialId" <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>/>
                <input id="kc-login" name="login" type="submit" value="${msg("doLogIn")}"
                       class="mt-6 min-h-11 w-full cursor-pointer rounded-md border border-accent bg-accent px-4 py-2 font-semibold text-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-foreground disabled:cursor-progress disabled:opacity-60" />
            </form>
        </#if>
    <#elseif section = "info">
        ${msg("agilinaInvitationOnly")}
    </#if>
</@layout.registrationLayout>
