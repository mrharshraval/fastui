"use client";

import Image from "next/image";
import { useState } from "react";

export function TrustedBy() {
  const clients = [
    { name: 'Plaid', domain: 'plaid.com' },
    { name: 'Svea', domain: 'svea.com' },
    { name: 'Mews', domain: 'mews.com' },
    { name: 'Moss', domain: 'moss.ai' },
    { name: 'Brand New Day', domain: 'brandnewday.nl' },
    { name: 'seQura', domain: 'sequra.com' },
    { name: 'Bolt', domain: 'bolt.eu' },
  ];
  
  const [failedLogos, setFailedLogos] = useState(new Set());

  return (
    <section className="py-12 bg-background text-foreground">
      <div className="container max-w-7xl mx-auto px-8 md:px-16 lg:px-20">
        <p className="text-center text-sm font-medium text-muted-foreground mb-8">
          Built for businesses where compliance matters
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 opacity-60 hover:opacity-100 transition-opacity duration-500">
          {clients.map((client) => {
            const hasFailed = failedLogos.has(client.domain);
            return (
              <div key={client.domain} className="flex items-center justify-center">
                {!hasFailed ? (
                  <img
                    src={`https://logo.clearbit.com/${client.domain}`}
                    alt={client.name}
                    className="h-8 md:h-10 object-contain grayscale hover:grayscale-0 transition-all duration-300"
                    onError={() => {
                      setFailedLogos((prev) => {
                        const next = new Set(prev);
                        next.add(client.domain);
                        return next;
                      });
                    }}
                  />
                ) : (
                  <span className="text-xl md:text-2xl font-bold tracking-tighter text-foreground">
                    {client.name}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
