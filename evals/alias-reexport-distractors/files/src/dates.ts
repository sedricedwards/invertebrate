export function format(d: Date): string {
  return d.toISOString().slice(0, 10);
}
