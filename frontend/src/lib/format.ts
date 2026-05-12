export function formatStreak(streak: number): string {
  if (streak === 0) return "—";
  return streak > 0 ? `W${streak}` : `L${Math.abs(streak)}`;
}
