// The oracle card count is always system-randomized, never user-picked —
// 3 to 9 cards inclusive (see CLAUDE.md).
export function randomOracleCount(): number {
  return Math.floor(Math.random() * 7) + 3;
}
