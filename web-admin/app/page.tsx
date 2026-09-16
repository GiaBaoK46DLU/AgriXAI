import { redirect } from "next/navigation";

import { getSessionToken } from "@/lib/session";

export default async function RootPage() {
  const token = await getSessionToken();
  redirect(token ? "/admin" : "/login");
}
