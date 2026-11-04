import * as users from "./user";

export function auditLine(u: users.User, action: string): string {
  return `${new Date().toISOString()} ${users.formatUser(u)} ${action}`;
}
