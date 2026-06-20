import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Mona AI Operations Hub",
  description: "Enterprise operations workflows for finance, HR, compliance, marketing and security.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

