import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ХанБио CRM",
  description: "Заявки, записи и клиенты реабилитационного центра",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
