/**
 * Formats a UTC ISO instant (e.g. game tipoff_at) as the viewer's LOCAL
 * calendar date in YYYY-MM-DD. Used for forward-looking surfaces so the date
 * reflects the user's own timezone rather than the stored UTC/ET day.
 */
export function formatLocalDate(iso: string): string {
  const d = new Date(iso);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}
