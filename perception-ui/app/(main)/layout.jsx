"use client"

import { Navbar } from "@/components/layout/navbar";
import { useAuthStore } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function MainLayout({ children }) {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const router = useRouter();

  useEffect(() => {
    // Check auth status on component mount
    checkAuth();
  }, [checkAuth]);

  useEffect(() => {
    // Redirect to login if not authenticated after loading
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  // Show a loading state while checking auth
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  // Render the layout if authenticated
  return isAuthenticated ? (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1 container py-8">{children}</main>
    </div>
  ) : null; // Render nothing while redirecting
}
