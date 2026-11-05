import { formatMoney } from "./index";

export const amountDue = (cents: number) => `Due ${formatMoney(cents)}`;
