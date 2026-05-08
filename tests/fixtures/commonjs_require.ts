const jwt = require('jsonwebtoken');
const hoek = require('hoek');
const { reach, clone } = require('hoek');
const AWS = require('aws-sdk');

function buildContext(token: string) {
  const payload = jwt.decode(token);
  const val = hoek.reach(payload, 'sub');
  return { userId: val };
}

function cloneConfig(cfg: object) {
  return clone(cfg);
}

function uploadFile(data: Buffer) {
  const s3 = new AWS.S3();
  return s3.putObject(data);
}
