"use client";

import * as DialogPrimitive from "@radix-ui/react-dialog";
import * as DropdownPrimitive from "@radix-ui/react-dropdown-menu";
import * as TabsPrimitive from "@radix-ui/react-tabs";
import { cva, type VariantProps } from "class-variance-authority";
import { X } from "lucide-react";
import * as React from "react";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex h-8 items-center justify-center gap-1.5 rounded-[5px] border px-3 text-[12px] font-medium transition-colors disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "border-brand bg-brand text-white hover:bg-[#103b2c]",
        outline: "border-[#cbd0c9] bg-white text-[#29312c] hover:bg-[#f5f6f4]",
        ghost: "border-transparent bg-transparent text-[#455049] hover:bg-[#ecefea]",
        danger: "border-[#e2bcbc] bg-[#fff0f0] text-[#9b2c2c] hover:bg-[#ffe5e5]",
      },
      size: { default: "h-8", sm: "h-7 px-2 text-[11px]", icon: "h-8 w-8 px-0" },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> {}
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, ...props }, ref) => (
  <button ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />
));
Button.displayName = "Button";

export function Badge({ children, tone = "neutral", className }: { children: React.ReactNode; tone?: "neutral" | "green" | "amber" | "red" | "blue"; className?: string }) {
  const tones = {
    neutral: "border-[#d6dad4] bg-[#f3f4f2] text-[#5b655f]",
    green: "border-[#badac9] bg-[#eaf6ef] text-[#246b4e]",
    amber: "border-[#ead49c] bg-[#fff6df] text-[#8a5b12]",
    red: "border-[#ebc2c2] bg-[#fff0f0] text-[#9b2c2c]",
    blue: "border-[#c9d7e8] bg-[#eef4fb] text-[#365e87]",
  };
  return <span className={cn("inline-flex h-5 items-center rounded-[4px] border px-1.5 text-[10px] font-semibold", tones[tone], className)}>{children}</span>;
}

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => (
  <input ref={ref} className={cn("h-8 w-full rounded-[5px] border border-[#cbd0c9] bg-white px-2.5 text-[12px] placeholder:text-[#929a95]", className)} {...props} />
));
Input.displayName = "Input";

export const Textarea = React.forwardRef<HTMLTextAreaElement, React.TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => (
  <textarea ref={ref} className={cn("min-h-20 w-full resize-y rounded-[5px] border border-[#cbd0c9] bg-white p-2.5 text-[12px]", className)} {...props} />
));
Textarea.displayName = "Textarea";

export function Select({ className, ...props }: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn("h-8 rounded-[5px] border border-[#cbd0c9] bg-white px-2.5 text-[12px]", className)} {...props} />;
}

export function Separator({ className }: { className?: string }) { return <div className={cn("h-px bg-line", className)} />; }
export function ScrollArea({ children, className }: { children: React.ReactNode; className?: string }) { return <div className={cn("overflow-auto", className)}>{children}</div>; }

export const Sheet = DialogPrimitive.Root;
export const SheetTrigger = DialogPrimitive.Trigger;
export function SheetContent({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/20" />
      <DialogPrimitive.Content className={cn("fixed inset-y-0 right-0 z-50 w-full max-w-[520px] border-l border-line bg-white shadow-xl", className)}>
        {children}
        <DialogPrimitive.Close className="absolute right-3 top-3 rounded p-1 text-muted hover:bg-[#f0f2ef]" aria-label="Close"><X size={16} /></DialogPrimitive.Close>
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  );
}

export const Tabs = TabsPrimitive.Root;
export const TabsList = ({ className, ...props }: React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>) => <TabsPrimitive.List className={cn("flex h-9 border-b border-line", className)} {...props} />;
export const TabsTrigger = ({ className, ...props }: React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>) => <TabsPrimitive.Trigger className={cn("border-b-2 border-transparent px-3 text-[12px] text-muted data-[state=active]:border-brand data-[state=active]:font-semibold data-[state=active]:text-brand", className)} {...props} />;
export const TabsContent = ({ className, ...props }: React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>) => <TabsPrimitive.Content className={cn("outline-none", className)} {...props} />;

export const DropdownMenu = DropdownPrimitive.Root;
export const DropdownMenuTrigger = DropdownPrimitive.Trigger;
export function DropdownMenuContent({ children }: { children: React.ReactNode }) {
  return <DropdownPrimitive.Portal><DropdownPrimitive.Content align="end" className="z-50 min-w-40 rounded-[5px] border border-line bg-white p-1 shadow-lg">{children}</DropdownPrimitive.Content></DropdownPrimitive.Portal>;
}
export function DropdownMenuItem(props: React.ComponentPropsWithoutRef<typeof DropdownPrimitive.Item>) {
  return <DropdownPrimitive.Item className="cursor-default rounded-[4px] px-2 py-1.5 text-[12px] outline-none hover:bg-[#f0f2ef]" {...props} />;
}

