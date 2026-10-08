import { toRoleLabel } from './role-label';

describe('toRoleLabel', () => {
  it('keeps the three labels the API sends', () => {
    expect(toRoleLabel('member')).toBe('member');
    expect(toRoleLabel('scrum_master')).toBe('scrum_master');
    expect(toRoleLabel('admin')).toBe('admin');
  });

  it('reads a label it does not know as member', () => {
    expect(toRoleLabel('product_owner')).toBe('member');
    expect(toRoleLabel('')).toBe('member');
  });
});
