#!/usr/bin/env node
"use strict";

// Run inside the Audiobookshelf 2.36 container. It uses the service's own
// signing secret only to mint a 60-second root access token, then creates the
// durable key through the supported API. No credential is printed.

const fs = require("fs");
const sqlite3 = require("sqlite3").verbose();
const jwt = require("jsonwebtoken");
const crypto = require("crypto");

const DB = "/config/absdatabase.sqlite";
const OUTPUT = "/config/astertv-jen-api-key.json";
const NAME = "AsterTV-Jen";
const BASE = "http://127.0.0.1:80";

function one(db, sql, params = []) {
  return new Promise((resolve, reject) =>
    db.get(sql, params, (error, row) => error ? reject(error) : resolve(row)));
}

async function main() {
  if (fs.existsSync(OUTPUT)) throw new Error("audiobookshelf-output-exists");
  const db = new sqlite3.Database(DB, sqlite3.OPEN_READONLY);
  try {
    const existing = await one(db, "select id from apiKeys where name=?", [NAME]);
    if (existing) throw new Error("audiobookshelf-key-already-exists");
    const root = await one(db,
      "select id,username from users where type='root' and isActive=1");
    const user = await one(db,
      "select id,username from users where username='jason' and isActive=1");
    const setting = await one(db,
      "select value from settings where key='server-settings'");
    if (!root || !user || !setting) throw new Error("audiobookshelf-identity-state");
    let settings = JSON.parse(setting.value);
    if (typeof settings === "string") settings = JSON.parse(settings);
    if (!settings || typeof settings.tokenSecret !== "string"
        || settings.tokenSecret.length < 32) {
      throw new Error("audiobookshelf-signing-state");
    }
    const access = jwt.sign({
      userId: root.id,
      username: root.username,
      jti: crypto.randomUUID(),
      type: "access",
    }, settings.tokenSecret, {expiresIn: 60});
    settings.tokenSecret = null;
    const response = await fetch(BASE + "/api/api-keys", {
      method: "POST",
      headers: {"Authorization": "Bearer " + access,
                "Content-Type": "application/json"},
      body: JSON.stringify({name: NAME, userId: user.id, isActive: true}),
    });
    if (response.status !== 200) {
      throw new Error("audiobookshelf-key-create-http-" + response.status);
    }
    const result = await response.json();
    const key = result && result.apiKey;
    if (!key || key.name !== NAME || key.userId !== user.id
        || key.isActive !== true || typeof key.apiKey !== "string"
        || key.apiKey.length < 32) {
      throw new Error("audiobookshelf-key-create-schema");
    }
    fs.writeFileSync(OUTPUT, JSON.stringify({
      api_key: key.apiKey,
      key_id: key.id,
      name: key.name,
      user_id_sha256: crypto.createHash("sha256").update(user.id).digest("hex"),
      username: user.username,
    }) + "\n", {mode: 0o600, flag: "wx"});
    console.log(JSON.stringify({created: true, name: NAME,
      user: user.username, credential_output: false}));
  } finally {
    db.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
