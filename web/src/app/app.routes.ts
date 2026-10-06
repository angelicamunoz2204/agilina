import { type Routes } from '@angular/router';

import { AppShell } from '@layout/app-shell/app-shell';
import { CenteredLayout } from '@layout/centered-layout/centered-layout';

/**
 * Screen map of the product. Every screen is lazy-loaded and arrives with the story that
 * builds it, inside the layout its mockup asks for: the team selector and its form in the
 * centered frame, the rest under the application header. The root shows the environment
 * status, which proves that the application talks to the API; /activate is the account
 * activation (HU-02).
 *
 * No route carries an access rule: the API decides who sees a team. That includes the team
 * settings, which only an admin may open: a guard would hide the API's 403, and the screen
 * shows "no access" with it.
 */
export const routes: Routes = [
  {
    path: 'teams',
    component: CenteredLayout,
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
        path: '',
        pathMatch: 'full',
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
        loadComponent: () =>
          import('@features/teams/presentation/team-dashboard-page').then(
            (m) => m.TeamDashboardPage,
          ),
        title: 'Agilina',
      },
      {
        // Settings → Team (HU-06): the members of the team, for its admins.
        path: 'teams/:teamId/settings',
        loadComponent: () =>
          import('@features/teams/presentation/team-settings-page').then((m) => m.TeamSettingsPage),
        title: 'Agilina',
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
