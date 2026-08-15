"use client";

import { useState } from "react";
import { Navigation } from "@/components/navigation";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CheckCircle2 } from "lucide-react";

export default function ContactPage() {
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    // Simulate form submission
    setIsSubmitted(true);
  };

  return (
    <>
      <Navigation />
      <main className="min-h-screen pt-32 pb-24 px-8 md:px-16 lg:px-20">
        <div className="container max-w-7xl mx-auto flex flex-col md:flex-row gap-16 lg:gap-32">
          
          {/* Left Column */}
          <div className="md:w-1/3 space-y-8">
            <h1 className="text-4xl md:text-5xl font-medium tracking-tight">
              Contact us
            </h1>
            <ul className="space-y-4 text-muted-foreground font-medium">
              <li className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Get a custom project proposal
              </li>
              <li className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Discuss timelines and deliverables
              </li>
              <li className="flex items-center gap-3">
                <CheckCircle2 className="w-5 h-5 text-primary" />
                Learn about our design process
              </li>
            </ul>
            <p className="text-sm text-muted-foreground pt-4">
              General inquiries? <a href="mailto:hello@fastui.com" className="text-foreground font-medium hover:underline transition-colors">Email hello@fastui.com</a>
            </p>
          </div>

          {/* Right Column */}
          <div className="md:w-2/3 max-w-2xl">
            {isSubmitted ? (
              <div className="bg-secondary/30 border border-border p-12 rounded-lg flex flex-col items-center text-center space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
                <CheckCircle2 className="w-16 h-16 text-primary" />
                <div className="space-y-2">
                  <h2 className="text-2xl font-medium tracking-tight">Inquiry Received</h2>
                  <p className="text-muted-foreground">
                    Thank you for reaching out. We will review your project details and get back to you shortly.
                  </p>
                </div>
                <Button onClick={() => setIsSubmitted(false)} variant="outline" className="mt-4">
                  Send another inquiry
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-8">
                <h3 className="text-xl font-medium mb-6">Tell us how we can help</h3>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="name" className="text-sm font-medium text-muted-foreground">Full name</Label>
                    <Input id="name" required className="bg-background/50 h-12 rounded-md" />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email" className="text-sm font-medium text-muted-foreground">Work email</Label>
                    <Input id="email" type="email" required className="bg-background/50 h-12 rounded-md" />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-muted-foreground">Company size</Label>
                    <Select required>
                      <SelectTrigger className="bg-background/50 h-12 rounded-md">
                        <SelectValue placeholder="Select..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1-10">1-10</SelectItem>
                        <SelectItem value="11-50">11-50</SelectItem>
                        <SelectItem value="51-200">51-200</SelectItem>
                        <SelectItem value="200+">200+</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="requirements" className="text-sm font-medium text-muted-foreground">Tell us about your requirements</Label>
                    <Textarea 
                      id="requirements" 
                      placeholder="I'm interested in FastUI for my team..." 
                      className="min-h-[120px] bg-background/50 rounded-md" 
                      required 
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row sm:items-center gap-6 pt-4">
                  <Button type="submit" className="w-full sm:w-auto rounded-full px-8 h-12 text-base shadow-none transition-all">
                    Send message
                  </Button>
                  <span className="text-sm text-muted-foreground">
                    You can also email us at <a href="mailto:sales@fastui.com" className="text-foreground hover:underline transition-colors border-b border-muted-foreground/30 pb-0.5">sales@fastui.com</a>
                  </span>
                </div>
              </form>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </>
  );
}
