import { type Routes } from '@angular/router';

/**
 * Screen map of the product. Every screen is lazy-loaded and arrives with the
 * story that builds it; for now only the environment status exists, which shows
 * that the application talks to the API.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('@features/status/presentation/status-page').then((m) => m.StatusPage),
    title: 'Agilina',
  },
  { path: '**', redirectTo: '' },
];
