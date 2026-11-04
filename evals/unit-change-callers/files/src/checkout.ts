import { parsePrice } from "./money";
import { createCharge } from "./payments";

/** createCharge takes an integer amount in cents (Stripe convention). */
export async function checkout(priceText: string, customerId: string) {
  const amount = parsePrice(priceText);
  return createCharge({ amount, currency: "usd", customer: customerId });
}
