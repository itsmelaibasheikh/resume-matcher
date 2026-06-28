"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export default function Navbar() {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "Home" },
    { href: "/scan", label: "Scan" },
    { href: "/dashboard", label: "Dashboard" },
  ];

  return (
    <nav
      className="w-full px-8 py-4 flex items-center justify-between border-b"
      style={{ backgroundColor: "#0d0d0f", borderColor: "#1e1e24" }}
    >
      <Link href="/" className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: "#7c3aed" }} />
        <span className="text-sm font-semibold tracking-tight text-white">
          ResuMatch
        </span>
      </Link>

      <div className="flex items-center gap-6">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="text-sm transition-colors duration-200"
            style={{
              color: pathname === link.href ? "#a78bfa" : "#6b7280",
            }}
          >
            {link.label}
          </Link>
        ))}

        <Link
          href="/scan"
          className="text-sm px-4 py-1.5 rounded-lg font-medium transition-all duration-200"
          style={{ backgroundColor: "#7c3aed", color: "#fff" }}
        >
          Try it →
        </Link>
      </div>
    </nav>
  );
}