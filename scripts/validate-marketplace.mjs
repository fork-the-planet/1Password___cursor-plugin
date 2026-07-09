#!/usr/bin/env node

import { readFileSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

function loadJSON(path) {
  return JSON.parse(readFileSync(path, "utf-8"));
}

const marketplaceSchema = loadJSON(
  resolve(root, "schemas/marketplace.schema.json")
);
const pluginSchema = loadJSON(resolve(root, "schemas/plugin.schema.json"));

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);

const validateMarketplace = ajv.compile(marketplaceSchema);
const validatePlugin = ajv.compile(pluginSchema);

let errors = 0;
let warnings = 0;

function fail(message) {
  console.error(`ERROR: ${message}`);
  errors++;
}

function warn(message) {
  console.warn(`WARN: ${message}`);
  warnings++;
}

function validateIdeMarketplace({ ide, manifestPath, pluginManifestDir, requirePlugins }) {
  if (!existsSync(manifestPath)) {
    if (requirePlugins) {
      fail(`${ide}: missing ${manifestPath}`);
    }
    return;
  }

  const marketplace = loadJSON(manifestPath);
  const label = `${ide} marketplace`;

  if (!marketplace.owner?.name) {
    fail(`${label}: owner.name is required`);
  }

  if (!validateMarketplace(marketplace)) {
    fail(`${label}: schema validation failed`);
    for (const err of validateMarketplace.errors) {
      console.error(`  ${err.instancePath || "/"}: ${err.message}`);
    }
  }

  const plugins = marketplace.plugins ?? [];

  if (requirePlugins && plugins.length === 0) {
    fail(`${label}: plugins must be a non-empty array`);
    return;
  }

  if (!requirePlugins && plugins.length === 0) {
    warn(`${label}: no plugins registered yet`);
    return;
  }

  for (const entry of plugins) {
    const pluginDir = resolve(root, entry.source);
    const pluginJsonPath = resolve(
      pluginDir,
      pluginManifestDir,
      "plugin.json"
    );

    if (!existsSync(pluginDir)) {
      fail(
        `${label}: plugin "${entry.name}" source directory "${entry.source}" does not exist`
      );
      continue;
    }

    if (!existsSync(pluginJsonPath)) {
      fail(
        `${label}: plugin "${entry.name}" missing ${pluginManifestDir}/plugin.json in "${entry.source}"`
      );
      continue;
    }

    const pluginJson = loadJSON(pluginJsonPath);

    if (!validatePlugin(pluginJson)) {
      fail(
        `${label}: plugin "${entry.name}" plugin.json schema validation failed (${entry.source}/${pluginManifestDir}/plugin.json):`
      );
      for (const err of validatePlugin.errors) {
        const detail =
          err.keyword === "additionalProperties"
            ? `${err.message}: "${err.params.additionalProperty}"`
            : err.message;
        console.error(`  ${err.instancePath || "/"}: ${detail}`);
      }
    }

    if (pluginJson.name && pluginJson.name !== entry.name) {
      fail(
        `${label}: plugin "${entry.name}" marketplace name does not match plugin.json name "${pluginJson.name}"`
      );
    }
  }
}

validateIdeMarketplace({
  ide: "Cursor",
  manifestPath: resolve(root, ".cursor-plugin/marketplace.json"),
  pluginManifestDir: ".cursor-plugin",
  requirePlugins: true,
});

validateIdeMarketplace({
  ide: "Claude Code",
  manifestPath: resolve(root, ".claude-plugin/marketplace.json"),
  pluginManifestDir: ".claude-plugin",
  requirePlugins: false,
});

if (errors > 0) {
  console.error(`\nValidation failed with ${errors} error(s).`);
  process.exit(1);
}

console.log(
  warnings > 0
    ? `Validation passed with ${warnings} warning(s).`
    : "All marketplace manifests validated successfully."
);
