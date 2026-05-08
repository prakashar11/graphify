import jwt from 'jsonwebtoken';
import * as fs from 'fs';
import { createHash } from 'crypto';

interface Context {
  userId: string;
}

function buildContext(token: string): Context {
  const payload = jwt.decode(token);
  const hash = createHash('sha256');
  return { userId: payload.sub };
}

function readConfig(path: string): string {
  return fs.readFileSync(path, 'utf-8');
}

function internalHelper(x: string): string {
  return buildContext(x).userId;
}
