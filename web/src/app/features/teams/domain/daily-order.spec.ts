import { keepMembers, moveDown, moveUp, toggleParticipant } from './daily-order';

describe('the order of the daily', () => {
  const order: readonly string[] = ['ana', 'bruno', 'carla'];

  describe('toggleParticipant', () => {
    it('adds a person at the end of the round', () => {
      expect(toggleParticipant(order, 'diego')).toEqual(['ana', 'bruno', 'carla', 'diego']);
    });

    it('adds the first person to an empty round', () => {
      expect(toggleParticipant([], 'ana')).toEqual(['ana']);
    });

    it('takes a person out and closes the gap', () => {
      expect(toggleParticipant(order, 'bruno')).toEqual(['ana', 'carla']);
    });

    it('leaves the list it gets untouched', () => {
      const original = [...order];

      toggleParticipant(order, 'bruno');
      toggleParticipant(order, 'diego');

      expect(order).toEqual(original);
    });
  });

  // ----------------------------------------------------------- criterion 4 --
  describe('moveUp', () => {
    it('gives the person the turn before theirs', () => {
      expect(moveUp(order, 'carla')).toEqual(['ana', 'carla', 'bruno']);
      expect(moveUp(order, 'bruno')).toEqual(['bruno', 'ana', 'carla']);
    });

    it('keeps the first person first', () => {
      expect(moveUp(order, 'ana')).toEqual(order);
    });

    it('changes nothing for someone who is not in the round', () => {
      expect(moveUp(order, 'diego')).toEqual(order);
    });

    it('leaves the list it gets untouched', () => {
      moveUp(order, 'carla');

      expect(order).toEqual(['ana', 'bruno', 'carla']);
    });
  });

  describe('moveDown', () => {
    it('gives the person the turn after theirs', () => {
      expect(moveDown(order, 'ana')).toEqual(['bruno', 'ana', 'carla']);
      expect(moveDown(order, 'bruno')).toEqual(['ana', 'carla', 'bruno']);
    });

    it('keeps the last person last', () => {
      expect(moveDown(order, 'carla')).toEqual(order);
    });

    it('changes nothing for someone who is not in the round', () => {
      expect(moveDown(order, 'diego')).toEqual(order);
    });

    it('leaves the list it gets untouched', () => {
      moveDown(order, 'ana');

      expect(order).toEqual(['ana', 'bruno', 'carla']);
    });
  });

  it('moving up and back down returns the same order', () => {
    expect(moveDown(moveUp(order, 'carla'), 'carla')).toEqual(order);
  });

  describe('keepMembers', () => {
    it('leaves out who is no longer a member and closes the gaps, keeping the order', () => {
      expect(keepMembers(['carla', 'ana', 'bruno'], ['ana', 'carla'])).toEqual(['carla', 'ana']);
    });

    it('keeps the whole round when everybody is still a member', () => {
      expect(keepMembers(order, ['carla', 'bruno', 'ana', 'diego'])).toEqual(order);
    });

    it('does not add a new member by itself', () => {
      expect(keepMembers(['ana'], ['ana', 'diego'])).toEqual(['ana']);
    });
  });
});
