"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchMe } from "../api/auth";
import type { Me } from "../api/types";

export function useMe() {
  return useQuery<Me, Error>({
    queryKey: ["me"],
    queryFn: fetchMe,
    retry: false,
  });
}
