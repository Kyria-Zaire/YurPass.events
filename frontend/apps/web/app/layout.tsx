import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "YurPass Web",
  description: "YurPass public web application",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <body className="antialiased">{children}</body>
    </html>
  );
}
