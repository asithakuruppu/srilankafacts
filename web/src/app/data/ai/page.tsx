import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Use with AI assistants",
  description: "Connect an AI assistant to Sri Lanka Facts through the read-only MCP server.",
  alternates: { canonical: "/data/ai" },
};

const CONFIG = `{
  "mcpServers": {
    "srilankafacts": {
      "command": "node",
      "args": ["/path/to/srilankafacts/mcp/dist/index.js"],
      "env": { "SLF_API_ROOT": "/path/to/a/release/folder" }
    }
  }
}`;

export default function AiPage() {
  return (
    <section className="shell section">
      <p className="eyebrow">
        <Link href="/data">Data</Link> · AI assistants
      </p>
      <h1>Use with AI assistants</h1>
      <p className="lede">
        A read-only Model Context Protocol (MCP) server lets an assistant look up places and
        numbers here and cite them. Every answer carries the unit, period, source and the
        release citation, and the server says &ldquo;not available&rdquo; instead of guessing.
      </p>

      <h2>Tools</h2>
      <dl className="facts">
        <div><dt>search_places</dt><dd>Find a place by name in English, Sinhala or Tamil.</dd></div>
        <div><dt>get_place_profile</dt><dd>All values for one place, each with its source.</dd></div>
        <div><dt>list_indicators</dt><dd>What is measured, with units and definitions.</dd></div>
        <div><dt>get_indicator</dt><dd>One indicator at one level, optionally inside an area, with totals for counts.</dd></div>
        <div><dt>compare_places</dt><dd>One indicator for two to ten places.</dd></div>
        <div><dt>get_sources</dt><dd>Licences, rights status, attribution and notices.</dd></div>
      </dl>

      <h2>Set it up</h2>
      <ol>
        <li>
          Build it once: <code>cd mcp &amp;&amp; pnpm install &amp;&amp; pnpm build</code>.
        </li>
        <li>
          Point <code>SLF_API_ROOT</code> at a release folder (the one holding <code>api/v1/</code>)
          or at this site&rsquo;s address.
        </li>
        <li>Add the server to your MCP client&rsquo;s configuration, for example:</li>
      </ol>
      <pre className="code-block"><code>{CONFIG}</code></pre>

      <h2>How well it answers</h2>
      <p>
        On a set of 150 questions drawn from the release (look-ups, comparisons, sums,
        definitions, and questions the data cannot answer), the tools returned the expected
        answer with a citation for all 150. That measures the server, not any assistant: how an
        assistant uses the tools still has to be checked separately.
      </p>

      <h2>Terms</h2>
      <p>
        The server is read-only and stores nothing about who asks. Census 2024 figures may be
        reused non-commercially with attribution while the Department of Census and Statistics
        has not published reuse terms. A plain-text summary for AI systems is at{" "}
        <a href="/llms.txt">/llms.txt</a>.
      </p>
    </section>
  );
}
