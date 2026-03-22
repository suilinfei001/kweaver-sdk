#!/usr/bin/env node

function exit(code) {
  if (process.stdout.writableNeedDrain || process.stderr.writableNeedDrain) {
    const done = () => {
      if (!process.stdout.writableNeedDrain && !process.stderr.writableNeedDrain) {
        process.exit(code);
      }
    };
    process.stdout.once("drain", done);
    process.stderr.once("drain", done);
  } else {
    process.exit(code);
  }
}

import("../dist/cli.js").then(({ run }) => {
  run(process.argv.slice(2))
    .then((code) => exit(code))
    .catch((err) => {
      console.error(err instanceof Error ? err.message : String(err));
      exit(1);
    });
});
