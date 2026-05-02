import { api, ensureCsrf } from "./client";
import type { Firm, Me } from "./types";

export interface SignupInput {
  email: string;
  password: string;
  firm_name: string;
  subdomain: string;
}

export interface SignupResponse {
  firm: Firm;
  redirect_url: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface LoginResponse {
  user: { email: string };
  role: string;
  firm: Firm;
}

export async function signup(input: SignupInput): Promise<SignupResponse> {
  await ensureCsrf();
  return api<SignupResponse>("/api/auth/signup", { method: "POST", body: input });
}

export async function login(input: LoginInput): Promise<LoginResponse> {
  await ensureCsrf();
  return api<LoginResponse>("/api/auth/login", { method: "POST", body: input });
}

export async function logout(): Promise<void> {
  await ensureCsrf();
  await api<void>("/api/auth/logout", { method: "POST" });
}

export async function fetchMe(): Promise<Me> {
  return api<Me>("/api/auth/me");
}
