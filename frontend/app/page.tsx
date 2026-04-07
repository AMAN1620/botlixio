import Link from "next/link";
import { Logo } from "@/components/Logo";
import {
  GlobeIcon,
  ZapIcon,
  BookOpenIcon,
  PaletteIcon,
  MessageCircleIcon,
  LanguagesIcon,
  TwitterIcon,
  LinkedInIcon,
  YouTubeIcon,
} from "@/components/icons/features";
import { SendIcon } from "@/components/icons";

/* ─── Navbar ─── */
function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-slate-200 bg-white/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-[1280px] items-center justify-between px-6 py-3 lg:px-[160px]">
        <Logo />
        <div className="hidden items-center gap-8 md:flex">
          <Link
            href="/"
            className="text-sm font-medium text-slate-900 hover:text-brand"
          >
            Home
          </Link>
          <Link
            href="#"
            className="text-sm font-medium text-slate-900 hover:text-brand"
          >
            Blog
          </Link>
          <Link
            href="#"
            className="text-sm font-medium text-slate-900 hover:text-brand"
          >
            Pricing
          </Link>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/login"
            className="px-4 py-2 text-sm font-bold text-slate-900 hover:text-brand"
          >
            Login
          </Link>
          <Link
            href="/register"
            className="rounded-lg bg-brand px-5 py-2.5 text-sm font-bold text-white hover:bg-brand/90"
          >
            Get Started
          </Link>
        </div>
      </div>
    </nav>
  );
}

/* ─── Hero ─── */
function Hero() {
  return (
    <section className="relative overflow-hidden px-6 py-24 lg:px-[160px] lg:py-32">
      {/* Decorative blurs */}
      <div className="pointer-events-none absolute inset-0 opacity-20">
        <div className="absolute -left-32 -top-20 h-[437px] w-[640px] rounded-full bg-brand/30 blur-[60px]" />
        <div className="absolute -bottom-20 -right-32 h-[437px] w-[640px] rounded-full bg-purple-500/20 blur-[60px]" />
      </div>

      <div className="relative mx-auto grid max-w-[1280px] items-center gap-16 lg:grid-cols-2">
        {/* Left – copy */}
        <div className="flex flex-col gap-8">
          <div className="flex flex-col gap-4">
            <h1 className="text-5xl font-black leading-[1] tracking-tight text-slate-900 lg:text-7xl">
              Create an AI chatbot for your{" "}
              <span className="text-brand">website in minutes</span>
            </h1>
            <p className="max-w-[540px] text-lg leading-7 text-slate-600 lg:text-xl lg:leading-8">
              Build, train, and deploy custom ChatGPT-like bots for your
              business in seconds without writing a single line of code.
            </p>
          </div>

          <div className="flex gap-4">
            <Link
              href="/register"
              className="rounded-xl bg-brand px-8 py-4 text-lg font-bold text-white shadow-[0_10px_15px_-3px_rgba(37,19,236,0.25),0_4px_6px_-4px_rgba(37,19,236,0.25)] hover:bg-brand/90"
            >
              Get Started
            </Link>
            <Link
              href="#"
              className="rounded-xl border border-slate-200 bg-white px-8 py-4 text-lg font-bold text-slate-900 hover:bg-slate-50"
            >
              View Demo
            </Link>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex -space-x-2">
              <div className="size-8 rounded-full border-2 border-white bg-slate-200" />
              <div className="size-8 rounded-full border-2 border-white bg-slate-300" />
              <div className="size-8 rounded-full border-2 border-white bg-slate-400" />
            </div>
            <p className="text-sm text-slate-500">
              Joined by 10,000+ businesses worldwide
            </p>
          </div>
        </div>

        {/* Right – chat preview */}
        <div className="relative mx-auto w-full max-w-[480px]">
          <div className="absolute -left-6 -top-6 size-32 rounded-full bg-brand/20 blur-[32px]" />
          <div className="absolute -bottom-6 -right-6 size-24 rounded-full bg-purple-500/20 blur-[20px]" />

          <div className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
            {/* Chat header */}
            <div className="flex items-center gap-3 border-b border-slate-100 pb-4">
              <div className="flex size-10 items-center justify-center rounded-full bg-brand-light">
                <svg
                  width="22"
                  height="19"
                  viewBox="0 0 22 19"
                  fill="none"
                  className="text-brand"
                >
                  <path
                    d="M7.9 18A9 9 0 1 0 4 14.1L2 20z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
              <div>
                <p className="text-base font-bold text-slate-900">
                  Botlixio Assistant
                </p>
                <div className="flex items-center gap-1">
                  <div className="size-2 rounded-full bg-green-500" />
                  <span className="text-xs text-green-500">Online</span>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex flex-col gap-4 py-6">
              {/* Bot message */}
              <div className="self-start rounded-b-2xl rounded-tr-2xl bg-slate-100 px-3 py-3">
                <p className="text-sm text-slate-900">
                  Hi there! How can I help you today?
                </p>
              </div>
              {/* User message */}
              <div className="self-end rounded-b-2xl rounded-tl-2xl bg-brand px-3 py-3">
                <p className="text-sm text-white">
                  Can you tell me more about your pricing plans?
                </p>
              </div>
              {/* Typing */}
              <div className="self-start rounded-b-2xl rounded-tr-2xl bg-slate-100 px-3 py-3">
                <p className="text-sm text-slate-900">Typing...</p>
              </div>
            </div>

            {/* Input */}
            <div className="flex items-center gap-2 border-t border-slate-100 pt-4">
              <div className="flex-1 rounded-lg bg-slate-100 px-4 py-2">
                <p className="text-sm text-slate-400">Write a message...</p>
              </div>
              <button className="flex size-10 items-center justify-center rounded-lg bg-brand text-white">
                <SendIcon className="size-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ─── Features ─── */
const features = [
  {
    icon: GlobeIcon,
    title: "Learns from website",
    desc: "Simply enter your URL and our AI indexes your entire site content automatically.",
  },
  {
    icon: ZapIcon,
    title: "Instant setup",
    desc: "Go live in under 2 minutes with our simple onboarding and visual editor.",
  },
  {
    icon: BookOpenIcon,
    title: "Knowledge base",
    desc: "Upload PDFs, docs, or text files to expand your bot\u2019s intelligence beyond the web.",
  },
  {
    icon: PaletteIcon,
    title: "Customization",
    desc: "Match your brand colors, icons, and personality with a fully white-labeled interface.",
  },
  {
    icon: MessageCircleIcon,
    title: "Welcome message",
    desc: "Engage visitors immediately with custom greetings based on the page they visit.",
  },
  {
    icon: LanguagesIcon,
    title: "Multi-language",
    desc: "Automatically support customers in over 100 languages with native-level accuracy.",
  },
];

function Features() {
  return (
    <section className="bg-white px-6 py-24 lg:px-[160px]">
      <div className="mx-auto max-w-[1280px]">
        <div className="mb-16 flex flex-col items-center gap-4">
          <span className="rounded-full bg-brand-light px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-brand">
            Features
          </span>
          <h2 className="max-w-[672px] text-center text-3xl font-bold tracking-tight text-slate-900 lg:text-4xl">
            Everything you need to automate customer support and lead generation
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-slate-200 bg-page-bg p-8 shadow-sm"
            >
              <div className="mb-6 flex size-12 items-center justify-center rounded-xl bg-brand-light">
                <f.icon className="size-5 text-brand" />
              </div>
              <h3 className="mb-2 text-xl font-bold text-slate-900">
                {f.title}
              </h3>
              <p className="leading-relaxed text-slate-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── How it Works ─── */
const steps = [
  {
    num: "1",
    title: "Add URL",
    desc: "Input your website link or upload technical documentation.",
  },
  {
    num: "2",
    title: "AI learns",
    desc: "Our AI processes your data to build a custom, secure knowledge base.",
  },
  {
    num: "3",
    title: "Embed code",
    desc: "Copy-paste a simple 1-line snippet to launch on your site.",
  },
];

function HowItWorks() {
  return (
    <section className="px-6 py-24 lg:px-[160px]">
      <div className="mx-auto max-w-[1280px]">
        <h2 className="mb-16 text-center text-3xl font-bold text-slate-900">
          Three simple steps to AI mastery
        </h2>

        <div className="relative grid gap-12 md:grid-cols-3">
          {/* Connector line */}
          <div className="absolute left-[15%] right-[15%] top-8 hidden h-0.5 bg-slate-200 md:block" />

          {steps.map((s) => (
            <div
              key={s.num}
              className="flex flex-col items-center gap-6 text-center"
            >
              <div className="relative flex size-16 items-center justify-center rounded-full bg-brand shadow-[0_20px_25px_-5px_rgba(37,19,236,0.2),0_8px_10px_-6px_rgba(37,19,236,0.2)]">
                <span className="text-2xl font-black text-white">
                  {s.num}
                </span>
              </div>
              <div>
                <h3 className="mb-2 text-xl font-bold text-slate-900">
                  {s.title}
                </h3>
                <p className="text-slate-600">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── FAQ ─── */
const faqs = [
  {
    q: "What data can I train my chatbot on?",
    a: "You can train your chatbot by providing a website URL, uploading PDF files, Word documents, or even just copy-pasting raw text. Our AI will analyze all the content to provide accurate answers.",
  },
  {
    q: "Can I integrate it with my existing tools?",
    a: "Yes! Botlixio offers native integrations with Slack, Discord, and WhatsApp, plus a robust API for custom integrations with your CRM or support helpdesk.",
  },
  {
    q: "How many languages does it support?",
    a: "Our AI models natively support over 100 languages. Your bot will automatically detect the visitor\u2019s language and respond accordingly.",
  },
];

function FAQ() {
  return (
    <section className="px-6 py-24 lg:px-[240px]">
      <div className="mx-auto max-w-[800px]">
        <h2 className="mb-12 text-center text-3xl font-bold text-slate-900">
          Frequently Asked Questions
        </h2>

        <div className="flex flex-col gap-4">
          {faqs.map((faq) => (
            <details
              key={faq.q}
              className="group rounded-xl border border-slate-200 bg-white"
            >
              <summary className="flex cursor-pointer items-center justify-between p-5 font-bold text-slate-900">
                {faq.q}
                <svg
                  className="size-3 shrink-0 transition-transform group-open:rotate-180"
                  viewBox="0 0 12 8"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="m1 1 5 5 5-5" />
                </svg>
              </summary>
              <p className="px-5 pb-5 text-sm leading-5 text-slate-600">
                {faq.a}
              </p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── CTA ─── */
function CTA() {
  return (
    <section className="px-6 lg:px-[160px]">
      <div className="relative mx-auto max-w-[1280px] overflow-hidden rounded-3xl bg-gradient-to-br from-brand to-purple-600 p-12 text-center">
        <div className="relative z-10 flex flex-col items-center gap-8">
          <h2 className="text-4xl font-black text-white lg:text-5xl">
            Launch your AI chatbot in minutes
          </h2>
          <p className="max-w-[576px] text-lg text-white/90">
            Join thousands of companies automating their support and capturing
            more leads today.
          </p>
          <Link
            href="/register"
            className="rounded-xl bg-white px-10 py-4 text-lg font-bold text-brand shadow-xl hover:bg-white/90"
          >
            Get Started
          </Link>
          <p className="text-sm text-white/75">
            No credit card required. Cancel anytime.
          </p>
        </div>
      </div>
    </section>
  );
}

/* ─── Footer ─── */
const footerLinks = {
  Product: ["Features", "Pricing", "Integrations", "Enterprise"],
  Company: ["About Us", "Careers", "Contact", "Blog"],
  Legal: ["Privacy Policy", "Terms of Service", "Cookie Policy", "Security"],
};

function Footer() {
  return (
    <footer className="mt-24 border-t border-slate-200 bg-white px-6 py-16 lg:px-[160px]">
      <div className="mx-auto max-w-[1280px]">
        <div className="grid gap-12 md:grid-cols-4">
          {/* Brand */}
          <div>
            <Logo />
            <p className="mt-4 text-sm leading-relaxed text-slate-500">
              The smarter way to build and manage custom AI chatbots for your
              modern business.
            </p>
            <div className="mt-6 flex gap-4">
              <Link href="#" className="text-slate-400 hover:text-slate-600">
                <TwitterIcon className="size-5" />
              </Link>
              <Link href="#" className="text-slate-400 hover:text-slate-600">
                <LinkedInIcon className="size-5" />
              </Link>
              <Link href="#" className="text-slate-400 hover:text-slate-600">
                <YouTubeIcon className="size-6" />
              </Link>
            </div>
          </div>

          {/* Link columns */}
          {Object.entries(footerLinks).map(([heading, links]) => (
            <div key={heading}>
              <h4 className="mb-4 text-sm font-bold uppercase tracking-widest text-slate-400">
                {heading}
              </h4>
              <ul className="flex flex-col gap-3">
                {links.map((link) => (
                  <li key={link}>
                    <Link
                      href="#"
                      className="text-sm text-slate-600 hover:text-brand"
                    >
                      {link}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-16 flex flex-col items-center justify-between gap-4 border-t border-slate-100 pt-8 md:flex-row">
          <p className="text-xs text-slate-500">
            &copy; 2024 Botlixio AI. All rights reserved.
          </p>
          <div className="flex gap-4 text-xs text-slate-500">
            <span>English (US)</span>
            <span>System Status</span>
          </div>
        </div>
      </div>
    </footer>
  );
}

/* ─── Page ─── */
export default function HomePage() {
  return (
    <div className="min-h-screen bg-page-bg font-sans">
      <Navbar />
      <Hero />
      <Features />
      <HowItWorks />
      <FAQ />
      <CTA />
      <Footer />
    </div>
  );
}
