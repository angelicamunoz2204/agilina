/**
 * The daily's participants are an ordered list of `userId`s: the position is the turn. These
 * functions return a new list and leave the one they get untouched.
 */

/** Adds the person at the end of the round, or takes them out and closes the gap. */
export function toggleParticipant(order: readonly string[], userId: string): readonly string[] {
  return order.includes(userId) ? order.filter((id) => id !== userId) : [...order, userId];
}

/** The person speaks one turn earlier; the first one stays first. */
export function moveUp(order: readonly string[], userId: string): readonly string[] {
  const index = order.indexOf(userId);
  if (index < 1) {
    return order;
  }
  return [
    ...order.slice(0, index - 1),
    userId,
    ...order.slice(index - 1, index),
    ...order.slice(index + 1),
  ];
}

/** The person speaks one turn later; the last one stays last. */
export function moveDown(order: readonly string[], userId: string): readonly string[] {
  const index = order.indexOf(userId);
  if (index === -1 || index === order.length - 1) {
    return order;
  }
  return [
    ...order.slice(0, index),
    ...order.slice(index + 1, index + 2),
    userId,
    ...order.slice(index + 2),
  ];
}

/** Only the people that are still members, in the same order, with the gaps closed. */
export function keepMembers(
  order: readonly string[],
  memberIds: readonly string[],
): readonly string[] {
  return order.filter((id) => memberIds.includes(id));
}
