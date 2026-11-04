export interface ChargeReq { amount: number; currency: string; customer: string }
/** amount: positive integer, smallest currency unit (cents). */
export async function createCharge(req: ChargeReq): Promise<{ id: string }> {
  if (!Number.isInteger(req.amount) || req.amount <= 0) throw new Error("amount must be integer cents");
  return { id: `ch_${req.customer}_${req.amount}` };
}
