import { Routes } from '@angular/router';

/**
 * Screen map of the product. Each route arrives with the story that builds it;
 * for now only the environment status one exists, which is what shows that the
 * application talks to the API.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/status/presentation/status-page').then((m) => m.StatusPage),
    title: 'Agilina',
  },
  { path: '**', redirectTo: '' },
];
