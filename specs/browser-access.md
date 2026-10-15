# Remembered browser access

The user requested a way to open the ordinary local URL without repeatedly using
the launch link. A connected browser is now remembered for 30 days by default.
The session survives an application restart and expires after a fixed duration.
The Account & privacy setting can disable remembering; local sign-out revokes it.

A new or expired browser shows an onboarding screen instead of a terminal-only
instruction. Its primary action asks the operating system on the server device to
open the existing private launch URL in its default browser. This action does not
return that URL, a secret or an authenticated cookie to the requesting browser.
If there is no desktop browser, or the user wants another browser, the same screen
accepts the initial launch link once. The fragment is removed from browser history
before network work. Later visits use the plain origin.

Security remains independent of loopback location and Codex login. Every API read
still requires a valid session except bootstrap and the bounded browser-open
action. Host/Origin checks cover both, and authenticated mutations require CSRF.
The browser-open action is rate limited. It opens only the fixed local launch URL;
there is no submitted URL or shell command. The launcher waits until the server
is accepting requests before opening the first browser window.

Remembered sessions store only a SHA-256 digest of a high-entropy random bearer
token, expiry, CSRF value, selected local account, runtime mode and usage-pause
state. Provider credentials remain outside browser sessions. Request budgets and
in-flight work authorizations are never restored. Revoked session objects cannot
reinsert a session from a late provider callback. Disabling remembering retains
only the current process session and uses a browser session cookie.

Verification includes actual application reconstruction with the same database,
restored access without bootstrap, zero restored provider budget, retained usage
pause, revocation after restart, tampered/expired cookies, runtime mode isolation,
CSRF rejection, local browser opening without secret disclosure, unavailable GUI
handling, and browser navigation/paste-link/remember/sign-out flows. A real
Chromium session also authenticated at the plain origin after the live server
process was replaced with a fresh bootstrap secret. Clicking a fragment-only
launch link in an already-open page is handled and covered by browser regression.
