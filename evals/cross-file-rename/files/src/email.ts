import { User, formatUser } from "./user";

export function greeting(u: User): string {
  return `Hi ${formatUser(u)},`;
}
