"use client"
import { Toaster as Sonner } from "sonner"
type ToasterProps = React.ComponentProps<typeof Sonner>
const Toaster = ({ ...props }: ToasterProps) => (
  <Sonner className="toaster group" toastOptions={{ classNames: { toast: "group toast", description: "group-[.toast]:text-zinc-500" } }} {...props} />
)
export { Toaster }
