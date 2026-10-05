import { type Routes } from '@angular/router';

/**
 * Screen map of the product. Every screen is lazy-loaded and arrives with the
 * story that builds it: today the environment status, which shows that the
 * application talks to the API, and the account activation (HU-02).
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
  { path: '**', redirectTo: '' },
];
