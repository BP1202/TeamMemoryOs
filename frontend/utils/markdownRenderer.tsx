/**
 * MarkdownRenderer — safely renders Markdown content as HTML.
 *
 * Security rules:
 *   - Never use dangerouslySetInnerHTML.
 *   - Uses react-markdown + rehype-sanitize with strict allow-list schema.
 *   - Only safe HTML elements allowed — no scripts, no event handlers.
 *   - AI-generated and user-generated content always passes through this.
 *
 * Features (Task 5 upgrade):
 *   - Code blocks with language label + copy-to-clipboard button.
 *   - Inline code, tables, blockquotes, lists styled via design system tokens.
 *   - Copy button: aria-label, keyboard accessible.
 *   - sanitizeSchema explicitly allows only approved tags.
 */

import { useState, type ReactNode } from 'react';
import ReactMarkdown, { type Components } from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeSanitize, { defaultSchema } from 'rehype-sanitize';
import { UtilityIcons } from '@config/icons';
import { cn } from '@utils/cn';

// ─── Strict sanitization schema ──────────────────────────────────────────────
// Extends defaultSchema for GFM table + code language class support.

const sanitizeSchema = {
  ...defaultSchema,
  tagNames: [
    ...(defaultSchema.tagNames ?? []),
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
  ],
  attributes: {
    ...defaultSchema.attributes,
    // Allow className (for code language labels) but nothing else
    '*': ['className'],
    code: ['className'],
  },
};

// ─── CopyButton ──────────────────────────────────────────────────────────────

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    // Clipboard API — no dangerouslySetInnerHTML, copies text only
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }).catch(() => {
      // Clipboard access denied — fail silently
    });
  };

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={copied ? 'Copied!' : 'Copy code to clipboard'}
      title={copied ? 'Copied!' : 'Copy code'}
      className={cn(
        'absolute top-2 right-2 p-1.5 rounded text-xs',
        'bg-surface-elevated border border-border text-text-muted',
        'hover:text-text-primary hover:bg-surface-subtle transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand',
      )}
      data-testid="copy-code-btn"
    >
      {copied ? (
        <UtilityIcons.ChevronRight className="h-3 w-3" aria-hidden="true" />
      ) : (
        <UtilityIcons.Copy className="h-3 w-3" aria-hidden="true" />
      )}
    </button>
  );
}

// ─── Custom components ────────────────────────────────────────────────────────

function buildComponents(): Components {
  return {
    // Code block: relative wrapper + language label + copy button
    pre({ children }) {
      // Extract raw text from the nested <code> child for the clipboard
      const codeChild = (children as React.ReactElement)?.props as
        | { children?: ReactNode; className?: string }
        | undefined;
      const codeText =
        typeof codeChild?.children === 'string' ? codeChild.children : '';
      const lang = (codeChild?.className ?? '').replace('language-', '') || '';

      return (
        <div className="relative group my-3" data-testid="code-block">
          {/* Language label */}
          {lang && (
            <span
              className="absolute top-2 left-3 text-[10px] font-mono text-text-muted select-none"
              aria-hidden="true"
            >
              {lang}
            </span>
          )}

          {/* Copy button — always present on code blocks */}
          <CopyButton text={codeText} />

          <pre
            className={cn(
              'overflow-x-auto rounded-lg p-4 text-sm font-mono',
              'bg-surface-subtle border border-border',
              lang ? 'pt-7' : '',
            )}
          >
            {children}
          </pre>
        </div>
      );
    },

    // Inline code
    code({ children, className }) {
      const isBlock = className?.startsWith('language-');
      if (isBlock) {
        // Inside a <pre> — render as plain code
        return <code className={className}>{children}</code>;
      }
      return (
        <code className="bg-surface-subtle px-1.5 py-0.5 rounded text-xs font-mono text-text-primary">
          {children}
        </code>
      );
    },
  };
}

const components = buildComponents();

// ─── Exported component ───────────────────────────────────────────────────────

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div
      className={cn(
        'prose prose-sm max-w-none',
        'prose-headings:text-text-primary prose-headings:font-semibold',
        'prose-p:text-text-primary prose-p:leading-relaxed',
        'prose-blockquote:border-l-brand prose-blockquote:text-text-secondary',
        'prose-a:text-brand prose-a:no-underline hover:prose-a:underline',
        'prose-strong:text-text-primary',
        'prose-ul:text-text-primary prose-ol:text-text-primary',
        'prose-li:text-text-primary',
        'prose-table:text-text-primary prose-th:text-text-primary prose-td:text-text-primary',
        // Custom code styles handled by the components override above
        '[&_pre]:!bg-transparent [&_pre]:!p-0 [&_pre]:!border-0 [&_pre]:!my-0',
        className,
      )}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[[rehypeSanitize, sanitizeSchema]]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
