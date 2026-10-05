import { isLevelEnabled } from './log-level';

describe('isLevelEnabled', () => {
  it('lets through the threshold and anything more severe', () => {
    expect(isLevelEnabled('warn', 'warn')).toBeTrue();
    expect(isLevelEnabled('error', 'warn')).toBeTrue();
  });

  it('drops anything less severe than the threshold', () => {
    expect(isLevelEnabled('info', 'warn')).toBeFalse();
    expect(isLevelEnabled('debug', 'info')).toBeFalse();
  });
});
