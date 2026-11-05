#!/usr/bin/env node
"use strict";

// Emergency rollback for the single named broker key. No credential is printed.

const sqlite3 = require("sqlite3").verbose();
const jwt = require("jsonwebtoken");
const crypto = require("crypto");

const DB = "/config/absdatabase.sqlite";
const NAME = "AsterPodcastRequestBroker";
const BASE = "http://127.0.0.1:80";

function one(db, sql, params = []) {
  return new Promise((resolve, reject) =>
    db.get(sql, params, (error, row) => error ? reject(error) : resolve(row)));
}

async function main() {
  const db = new sqlite3.Database(DB, sqlite3.OPEN_READONLY);
  try {
    const key = await one(db, "select id,name from apiKeys where name=?", [NAME]);
    if (!key) {
      console.log(JSON.stringify({revoked: false, state: "absent", name: NAME}));
      return;
    }
    const root = await one(db, "select id,username from users where type='root' and isActive=1");
    const setting = await one(db, "select value from settings where key='server-settings'");
    if (!root || !setting) throw new Error("audiobookshelf-identity-state");
    let settings = JSON.parse(setting.value);
    if (typeof settings === "string") settings = JSON.parse(settings);
    if (!settings || typeof settings.tokenSecret !== "string" || settings.tokenSecret.length < 32) {
      throw new Error("audiobookshelf-signing-state");
    }
    const access = jwt.sign({userId: root.id, username: root.username,
      jti: crypto.randomUUID(), type: "access"}, settings.tokenSecret, {expiresIn: 60});
    settings.tokenSecret = null;
    const response = await fetch(BASE + "/api/api-keys/" + encodeURIComponent(key.id), {
      method: "DELETE", headers: {"Authorization": "Bearer " + access},
    });
    if (response.status !== 200) throw new Error("audiobookshelf-key-delete-http-" + response.status);
    console.log(JSON.stringify({revoked: true, name: NAME, credential_output: false}));
  } finally { db.close(); }
}

main().catch((error) => { console.error(error.message); process.exit(1); });
