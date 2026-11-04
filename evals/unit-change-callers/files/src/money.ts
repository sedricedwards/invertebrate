/** Parse a user-entered price like "12.34" or "$12.34". Returns dollars. */
export function parsePrice(input: string): number {
  return Number(input.replace(/[$,]/g, ""));
}
