import { parsePrice } from "./money";

export function lineTotal(priceText: string, qty: number): string {
  return `$${(parsePrice(priceText) * qty).toFixed(2)}`;
}
