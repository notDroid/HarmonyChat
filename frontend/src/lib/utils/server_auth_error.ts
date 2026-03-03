"use server";

import { clearSession } from "../auth/session";
import { redirect } from "next/navigation";
import { getAccesstToken, getRefreshToken } from "../auth/session";

export default async function handleServerAuthError() {
  if (await getAccesstToken() || await getRefreshToken()) {
    await clearSession();
    redirect('/login');
  }
}