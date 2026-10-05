import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Header } from '../header/header';

/** Frame of the screens that live inside the application: the header above the screen. */
@Component({
  selector: 'agl-app-shell',
  imports: [RouterOutlet, Header],
  templateUrl: './app-shell.html',
})
export class AppShell {}
