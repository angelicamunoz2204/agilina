import { computed, effect, inject, Injectable, signal, type Signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { ShellContext, type ShellTeam } from '@core/shell/shell-context';

import { TeamsPort } from './teams.port';
import { UsersPort } from './users.port';

/**
 * What the top bar says about the team of a screen: the team's name and how the user is
 * called in it (their label in this team) and the person's own name, both from `GET /v1/users/me`. It is put in the bar while
 * the screen lives and taken out when the screen goes away. If either cannot be read the bar
 * simply says nothing about the team: the screen already tells what went wrong. Provided by
 * the page, so it lives and dies with it.
 */
@Injectable()
export class TeamShellFacade {
  private readonly teamsPort = inject(TeamsPort);
  private readonly usersPort = inject(UsersPort);
  private readonly shell = inject(ShellContext);
  private readonly teamId = signal<Signal<string> | null>(null);
  private readonly team = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.teamsPort.get(params),
  });
  private readonly me = rxResource({
    params: () => this.teamId()?.(),
    stream: ({ params }) => this.usersPort.me(params),
  });
  private readonly entry = computed<ShellTeam | null>(() =>
    this.team.hasValue() && this.me.hasValue()
      ? {
          name: this.team.value().name,
          roleLabel: this.me.value().label,
          userName: this.me.value().fullName,
        }
      : null,
  );

  constructor() {
    effect((onCleanup) => {
      const entry = this.entry();
      if (entry === null) {
        return;
      }
      this.shell.enter(entry);
      onCleanup(() => {
        this.shell.leave(entry);
      });
    });
  }

  follow(teamId: Signal<string>): void {
    this.teamId.set(teamId);
  }
}
