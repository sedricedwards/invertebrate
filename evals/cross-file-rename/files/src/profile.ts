import { User, formatUserName } from "./user";

export function profileHeader(u: User): string {
  return `<h1>${formatUserName(u)}</h1>`;
}
