import { Routes } from '@angular/router';

/**
 * Mapa de pantallas del producto. Cada ruta llega con la historia que la
 * construye; por ahora solo existe la de estado del entorno, que es lo que
 * demuestra que la aplicación habla con la API.
 */
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./paginas/estado/estado').then((m) => m.Estado),
    title: 'Agilina',
  },
  { path: '**', redirectTo: '' },
];
