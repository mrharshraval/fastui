"use client";

import Image from "next/image";
import { useState } from "react";

export function TrustedByLeaders() {
  const clients = [
    { name: 'Moss', domain: 'moss.ai' },
    { name: 'Plaid', domain: 'plaid.com' },
    { name: 'Stripe', domain: 'stripe.com' },
    { name: 'Qonto', domain: 'qonto.com' },
    { name: 'Remote', domain: 'remote.com' },
  ];

  const [failedLogos, setFailedLogos] = useState(new Set());

  return (
    <section className="py-24 px-8 md:px-16 lg:px-20 bg-background text-foreground">
      <div className="container max-w-7xl mx-auto flex flex-col items-center">
        
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-medium tracking-tight">
            Trusted by leaders
          </h2>
          <p className="text-muted-foreground text-lg max-w-xl mx-auto leading-relaxed">
            Run your business onboarding like the world's best companies — <br className="hidden md:block" /> without needing a 100+ people team.
          </p>
        </div>

        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 mb-16 opacity-50 hover:opacity-100 transition-opacity duration-500">
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
                  <span className="text-2xl md:text-3xl font-bold tracking-tighter text-foreground">
                    {client.name}
                  </span>
                )}
              </div>
            );
          })}
        </div>

        <div className="w-full bg-gray-10 rounded-[40px] overflow-hidden flex flex-col md:flex-row border border-border/20">
          {/* Testimonial Content */}
          <div className="flex-1 p-10 md:p-16 lg:p-20 flex flex-col justify-between space-y-16">
            <p className="text-2xl md:text-[28px] font-medium leading-snug tracking-tight text-foreground/90">
              “People ask how we're using AI in compliance and I have a simple answer for them. We use FastUI.”
            </p>
            <div className="space-y-1">
              <p className="font-semibold text-sm text-foreground/90">Zak Lambert</p>
              <p className="text-muted-foreground text-sm">GM EMEA, Plaid</p>
            </div>
          </div>
          
          {/* Image Placeholder */}
          <div className="md:w-[45%] min-h-[400px] bg-secondary relative flex items-center justify-center">
             <span className="text-muted-foreground font-medium relative z-10">[Image of Zak Lambert]</span>
          </div>
        </div>

      </div>
    </section>
  );
}
