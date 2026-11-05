import { format as fmt } from "./money";

export const totalLine = (cents: number) => "Total: " + fmt(cents);
