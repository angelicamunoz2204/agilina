import { type Routes } from '@angular/router';

/**
 * Screen map of the product. Every screen is lazy-loaded and arrives with the
 * story that builds it. The root shows the environment status, which proves that
 * the application talks to the API; /activar is the account activation (HU-02).
 *
 * No route carries an access rule: the API decides who sees a team. 'teams/new'
 * goes before 'teams/:teamId' so that it is never read as a team id.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('@features/status/presentation/status-page').then((m) => m.StatusPage),
    title: 'Agilina',
  },
  {
    // The activation link of the invitation email: /activar#t=<token>.
    path: 'activar',
    loadComponent: () =>
      import('@features/identity/presentation/activate-page').then((m) => m.ActivatePage),
    title: 'Agilina',
  },
  {
    path: 'teams',
    loadComponent: () =>
      import('@features/teams/presentation/team-selector-page').then((m) => m.TeamSelectorPage),
    title: 'Agilina',
  },
  {
    path: 'teams/new',
    loadComponent: () =>
      import('@features/teams/presentation/create-team-page').then((m) => m.CreateTeamPage),
    title: 'Agilina',
  },
  {
    path: 'teams/:teamId',
    loadComponent: () =>
      import('@features/teams/presentation/team-dashboard-page').then((m) => m.TeamDashboardPage),
    title: 'Agilina',
  },
  { path: '**', redirectTo: '' },
];
