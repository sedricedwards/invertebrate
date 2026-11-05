import { format } from "./money";

export const receiptLine = (cents: number) => format(cents, "USD");
