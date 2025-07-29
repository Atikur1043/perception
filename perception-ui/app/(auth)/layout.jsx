import { Navbar } from "@/components/layout/navbar";

export default function AuthLayout({ children }) {
  // This component wraps the login/signup pages to provide a consistent navbar
  // for unauthenticated users, making the pages feel less empty.
  return (
    <div className="relative flex min-h-screen flex-col">
      <Navbar />
      <main className="flex-1">{children}</main>
    </div>
  );
}
