import { adminLabelOf } from './admin-label';

describe('adminLabelOf', () => {
  it('is the label the list gives the admin role', () => {
    expect(
      adminLabelOf([
        { role: 'admin', label: 'scrum_master' },
        { role: 'member', label: 'member' },
      ]),
    ).toBe('scrum_master');
  });

  it('is admin in an autonomous team', () => {
    expect(adminLabelOf([{ role: 'admin', label: 'admin' }])).toBe('admin');
  });

  it('is the plain word before the list arrives', () => {
    expect(adminLabelOf([])).toBe('admin');
  });
});
