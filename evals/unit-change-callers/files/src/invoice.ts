import { parsePrice } from "./money";

export function invoiceLine(desc: string, priceText: string): string {
  const cents = parsePrice(priceText);
  return `${desc.padEnd(30)} $${(cents / 100).toFixed(2)}`;
}
