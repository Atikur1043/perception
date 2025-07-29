import { Inter } from "next/font/google";
import "./globals.css";
import { ClientLayout } from "./client-layout"; // Import our new client layout

const inter = Inter({ subsets: ["latin"] });

// Your metadata now lives here, in a Server Component!
export const metadata = {
  title: "Perception",
  description: "AI-Powered Online Evaluation Portal",
  icons: {
    icon: "/logo192.png", // This points to public/logo.png
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        {/* The ClientLayout now wraps the children to provide all the client-side context */}
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}
