import { type Routes } from '@angular/router';

import { authGuard, entranceGuard } from '@core/auth/auth.guard';
import { AppShell } from '@layout/app-shell/app-shell';
import { CenteredLayout } from '@layout/centered-layout/centered-layout';

/**
 * Screen map of the product. Every screen is lazy-loaded and arrives with the story that
 * builds it, inside the layout its mockup asks for: the team selector and its form in the
 * centered frame, the rest under the application header.
 *
 * Public screens: /activate (the account activation, HU-02) and /status (the environment
 * status, which proves that the application talks to the API). The entrance, /, sends the
 * signed-in to their teams and everybody else to sign in (HU-03). The routes of the teams
 * need a session: the guard takes the person to sign in and brings them back to the page
 * they asked for. It is comfort, not security: the API decides who sees a team.
 */
export const routes: Routes = [
  {
    path: 'teams',
    component: CenteredLayout,
    canActivate: [authGuard],
    children: [
      {
        path: '',
        loadComponent: () =>
          import('@features/teams/presentation/team-selector-page').then((m) => m.TeamSelectorPage),
        title: 'Agilina',
      },
      {
        // Before any team id, so that it is never read as one.
        path: 'new',
        loadComponent: () =>
          import('@features/teams/presentation/create-team-page').then((m) => m.CreateTeamPage),
        title: 'Agilina',
      },
    ],
  },
  {
    path: '',
    component: AppShell,
    children: [
      {
        // Never renders: the guard always sends the person somewhere else.
        path: '',
        pathMatch: 'full',
        canActivate: [entranceGuard],
        children: [],
      },
      {
        path: 'status',
        loadComponent: () =>
          import('@features/status/presentation/status-page').then((m) => m.StatusPage),
        title: 'Agilina',
      },
      {
        // The activation link of the invitation email: /activate#t=<token>.
        path: 'activate',
        loadComponent: () =>
          import('@features/identity/presentation/activate-page').then((m) => m.ActivatePage),
        title: 'Agilina',
      },
      {
        path: 'teams/:teamId',
        canActivate: [authGuard],
        loadComponent: () =>
          import('@features/teams/presentation/team-dashboard-page').then(
            (m) => m.TeamDashboardPage,
          ),
        title: 'Agilina',
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
