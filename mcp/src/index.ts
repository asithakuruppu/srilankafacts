#!/usr/bin/env node
/**
 * stdio entry point. SLF_API_ROOT is a local release folder (holding api/v1/) or the site's
 * base URL; SLF_SITE_URL, if set, is used for place links in answers.
 */
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

import { StaticApi } from "./api.js";
import { createServer } from "./server.js";

const root = process.env.SLF_API_ROOT;
if (!root) {
  console.error("Set SLF_API_ROOT to a release folder (with api/v1/) or the site's base URL.");
  process.exit(1);
}
const server = createServer(new StaticApi(root, process.env.SLF_SITE_URL ?? null));
await server.connect(new StdioServerTransport());
