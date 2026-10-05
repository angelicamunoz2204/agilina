import { type Observable } from 'rxjs';

import { type ActivatedAccount, type Invitation } from '../domain/invitation';

/**
 * Port towards the invitations of the API. A failure arrives as an `InvitationFailure`
 * error, never as an HTTP detail. An abstract class so that it doubles as the injection
 * token; the HTTP adapter is bound in app.config.ts.
 */
export abstract class InvitationPort {
  /** The invitation behind a link that still works. A used, expired or altered one fails. */
  abstract status(token: string): Observable<Invitation>;
  abstract activate(
    token: string,
    password: string,
    confirmation: string,
  ): Observable<ActivatedAccount>;
  /** Tells the team's admins that this person needs a new invitation. */
  abstract requestNew(token: string): Observable<void>;
}
