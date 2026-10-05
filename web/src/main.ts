import { bootstrapApplication } from '@angular/platform-browser';

import { loadRuntimeConfig } from '@core/config/load-runtime-config';

import { App } from './app/app';
import { createAppConfig } from './app/app.config';

// The runtime config is loaded first so that every provider can read it
// synchronously. Nothing else exists yet, hence the console.
loadRuntimeConfig()
  .then((runtimeConfig) => bootstrapApplication(App, createAppConfig(runtimeConfig)))
  .catch((error: unknown) => {
    console.error('Agilina could not start', error);
  });
