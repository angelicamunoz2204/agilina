import { TestBed } from '@angular/core/testing';

import { ShellContext } from './shell-context';

describe('ShellContext', () => {
  let shell: ShellContext;

  beforeEach(() => {
    shell = TestBed.inject(ShellContext);
  });

  it('starts without a team', () => {
    expect(shell.team()).toBeNull();
  });

  it('holds the team a screen entered and forgets it when that screen leaves', () => {
    const atlas = { name: 'Atlas', roleLabel: 'scrum_master', userName: 'Ana Gil' };

    shell.enter(atlas);
    expect(shell.team()).toBe(atlas);

    shell.leave(atlas);
    expect(shell.team()).toBeNull();
  });

  it('does not forget a team that another screen entered after', () => {
    const atlas = { name: 'Atlas', roleLabel: 'scrum_master', userName: 'Ana Gil' };
    const nova = { name: 'Nova', roleLabel: 'admin', userName: 'Ana Gil' };
    shell.enter(atlas);
    shell.enter(nova);

    shell.leave(atlas);

    expect(shell.team()).toBe(nova);
  });
});
