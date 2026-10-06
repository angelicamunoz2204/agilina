import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

/** Root component. The frame around each screen is a layout chosen by its route. */
@Component({
  selector: 'agl-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
})
export class App {}
