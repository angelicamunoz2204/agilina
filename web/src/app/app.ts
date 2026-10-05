import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { Header } from '@layout/header/header';

/** Root component: the layout around the routed screen. */
@Component({
  selector: 'agl-root',
  imports: [RouterOutlet, Header],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {}
